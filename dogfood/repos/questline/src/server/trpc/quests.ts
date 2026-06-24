// Quest tRPC router — create & complete.
//
// Enforces the freemium gate (3 active quests on FREE) and emits tracked
// events for every meaningful action.

import { z } from "zod";
import { TRPCError } from "@trpc/server";
import { router, protectedProcedure } from "./trpc";
import { prisma } from "../../lib/db";
import { track } from "../../lib/analytics";
import { computeStreak } from "../streaks";

const FREE_ACTIVE_QUEST_LIMIT = 3;

const createInput = z.object({
  title: z.string().min(1).max(120),
  cadence: z.enum(["DAILY", "WEEKLY", "N_PER_WEEK"]).default("DAILY"),
  perWeek: z.number().int().min(1).max(7).optional(),
});

const completeInput = z.object({
  questId: z.string().cuid(),
});

export const questsRouter = router({
  create: protectedProcedure
    .input(createInput)
    .mutation(async ({ ctx, input }) => {
      const user = ctx.user;

      if (user.plan === "FREE") {
        const active = await prisma.quest.count({
          where: { userId: user.id, archived: false },
        });
        if (active >= FREE_ACTIVE_QUEST_LIMIT) {
          await track("freemium_gate_hit", {
            userId: user.id,
            props: { gate: "active_quests", limit: FREE_ACTIVE_QUEST_LIMIT },
          });
          throw new TRPCError({
            code: "FORBIDDEN",
            message: "Free plan is limited to 3 active quests. Upgrade to add more.",
          });
        }
      }

      const quest = await prisma.quest.create({
        data: {
          userId: user.id,
          title: input.title,
          cadence: input.cadence,
          perWeek: input.cadence === "N_PER_WEEK" ? input.perWeek : null,
          streak: { create: {} },
        },
      });

      await track("quest_created", {
        userId: user.id,
        props: { questId: quest.id, cadence: quest.cadence },
      });

      return quest;
    }),

  complete: protectedProcedure
    .input(completeInput)
    .mutation(async ({ ctx, input }) => {
      const user = ctx.user;
      const quest = await prisma.quest.findFirst({
        where: { id: input.questId, userId: user.id },
        include: { completions: true, streak: true },
      });
      if (!quest) {
        throw new TRPCError({ code: "NOT_FOUND", message: "Quest not found" });
      }

      const completion = await prisma.questCompletion.create({
        data: { questId: quest.id },
      });

      const result = computeStreak(
        [...quest.completions, completion].map((c) => ({
          completedAt: c.completedAt,
          timezone: user.timezone,
        })),
      );

      const prev = quest.streak?.current ?? 0;
      await prisma.streak.update({
        where: { questId: quest.id },
        data: {
          current: result.current,
          longest: Math.max(result.longest, quest.streak?.longest ?? 0),
          lastCompleted: completion.completedAt,
        },
      });

      const xpGain = 10 + Math.min(result.current, 7) * 2; // streak multiplier
      await prisma.quest.update({
        where: { id: quest.id },
        data: { xp: { increment: xpGain } },
      });

      await track("quest_completed", {
        userId: user.id,
        props: { questId: quest.id, xpGain, streak: result.current },
      });
      if (result.current > prev) {
        await track("streak_extended", {
          userId: user.id,
          props: { questId: quest.id, streak: result.current },
        });
      }

      return { xpGain, streak: result.current };
    }),
});
