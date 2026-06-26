// Quests list — Next.js App Router server component.
// Lists the signed-in user's active quests with streak + XP.

import { prisma } from "../../lib/db";
import { getSessionUser } from "../../lib/session";
import { isEnabled } from "../../lib/flags";
import { track } from "../../lib/analytics";

export const dynamic = "force-dynamic";

export default async function QuestsPage() {
  const user = await getSessionUser();
  if (!user) {
    return <main className="p-8">Please sign in to see your quests.</main>;
  }

  const quests = await prisma.quest.findMany({
    where: { userId: user.id, archived: false },
    include: { streak: true },
    orderBy: { createdAt: "asc" },
  });

  const guildsEnabled = isEnabled("guildsV1", user.id);
  await track("onboarding_step_viewed", {
    userId: user.id,
    props: { page: "quests", questCount: quests.length },
  });

  return (
    <main className="p-8">
      <header className="flex items-baseline justify-between">
        <h1 className="text-2xl font-bold">Your quests</h1>
        {guildsEnabled && (
          <a href="/guilds" className="text-sm underline">
            Guilds
          </a>
        )}
      </header>

      {quests.length === 0 ? (
        <p className="mt-6 text-gray-500">
          No quests yet. Create your first one to start a streak.
        </p>
      ) : (
        <ul className="mt-6 space-y-3">
          {quests.map((q) => (
            <li
              key={q.id}
              className="flex items-center justify-between rounded-lg border p-4"
            >
              <div>
                <p className="font-medium">{q.title}</p>
                <p className="text-sm text-gray-500">{q.cadence.toLowerCase()}</p>
              </div>
              <div className="text-right text-sm">
                <p>🔥 {q.streak?.current ?? 0} day streak</p>
                <p className="text-gray-500">{q.xp} XP</p>
              </div>
            </li>
          ))}
        </ul>
      )}
    </main>
  );
}
