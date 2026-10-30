/* Settings ▸ Calls ▸ Line ▸ The line ▸ Telnyx: the Set up Telnyx fold
 * (LINE-3b, LINE design §8). Three steps, each one press:
 *
 *   1. Your key: the write-only key row (the keystore word);
 *   2. Connect: the hub makes the SIP account (`POST …/telnyx/connect`);
 *   3. A number: an area code, Find numbers, up to 10 rows with the monthly
 *      and upfront cost as Tokens; Buy goes through the kit's ConfirmVerb,
 *      and only its confirm sends the hub's quote (money: his press). The
 *      hub then points the number at the line (`…/assign`).
 *
 * The balance is a muted fact. A refusal says what failed, what is kept
 * and the next action, in the hub's own words. */
import { useCallback, useEffect, useState, type ReactNode } from "react";
import { Button } from "../../components/signal/Signal";
import { FoldGadget, StringGadget } from "../surface/gadgets";
import { ConfirmVerb } from "../surface/Surface";
import { DotWord } from "../surface/kit";
import { Token } from "../surface/Token";
import {
  assignTelnyxNumber, buyTelnyxNumber, connectTelnyx, findTelnyxNumbers, readTelnyxStatus, telnyxRefusal,
} from "./api";
import type { TelnyxNumber, TelnyxRefusal, TelnyxStatus } from "./types";

/** `+12125550100` → `+1 212 555 0100`; another shape stays as it is. */
export function phoneWords(number: string): string {
  const match = /^\+1(\d{3})(\d{3})(\d{4})$/.exec(number);
  return match ? `+1 ${match[1]} ${match[2]} ${match[3]}` : number;
}

/** `1.00`, `USD` → `$1.00`; another currency keeps its code. */
export function moneyWords(amount: string, currency: string): string {
  return currency === "USD" ? `$${amount}` : `${amount} ${currency}`;
}

function Step({ name, fact, verb, testId }: { name: ReactNode; fact?: ReactNode; verb?: ReactNode; testId: string }) {
  return (
    <div className="line-row telnyx-step" data-testid={testId}>
      <span className="line-row-name">{name}</span>
      <span className="line-row-fact">{fact}</span>
      <span className="line-row-state" />
      <span className="line-row-verb">{verb}</span>
    </div>
  );
}

export function TelnyxSetup({ keyRow, onChanged }: { keyRow: ReactNode; onChanged?(): void | Promise<void> }) {
  const [status, setStatus] = useState<TelnyxStatus | null>(null);
  const [busy, setBusy] = useState("");
  const [failure, setFailure] = useState<TelnyxRefusal | null>(null);
  const [area, setArea] = useState("");
  const [numbers, setNumbers] = useState<TelnyxNumber[] | null>(null);
  const [bought, setBought] = useState("");
  const [open] = useState(true);

  const load = useCallback(async () => {
    try { setStatus(await readTelnyxStatus()); } catch (error) { setFailure(telnyxRefusal(error)); }
  }, []);
  useEffect(() => { void load(); }, [load]);

  const press = async (name: string, work: () => Promise<void>) => {
    setBusy(name);
    setFailure(null);
    try { await work(); } catch (error) { setFailure(telnyxRefusal(error)); } finally { setBusy(""); }
  };

  const connect = () => press("connect", async () => {
    await connectTelnyx();
    await load();
    await onChanged?.();
  });
  const find = () => press("find", async () => { setNumbers(await findTelnyxNumbers(area.trim())); });
  const assign = (number: string) => press("assign", async () => {
    await assignTelnyxNumber(number);
    setBought("");
    setNumbers(null);
    await load();
    await onChanged?.();
  });
  const buy = (row: TelnyxNumber) => press(`buy-${row.phone_number}`, async () => {
    await buyTelnyxNumber(row);
    setBought(row.phone_number);
    await assignTelnyxNumber(row.phone_number);
    setBought("");
    setNumbers(null);
    await load();
    await onChanged?.();
  });

  const keyThere = Boolean(status && status.key !== "missing");
  const connection = status?.connection ?? null;
  const yours = status?.number ?? "";
  const token = yours ? "Number assigned" : connection ? "Connected" : keyThere ? "Key saved" : "Not set up";
  const areaOk = /^\d{3}$/.test(area.trim());

  return (
    <FoldGadget title="Set up Telnyx" token={token} open={open} className="telnyx-setup">
      <div className="telnyx-steps" data-testid="telnyx-setup" data-done={yours ? "" : undefined}>
        <div className="telnyx-key" data-testid="telnyx-step-key">
          <span className="telnyx-step-name">1. Your key</span>
          {keyRow}
        </div>

        <Step testId="telnyx-step-connect" name="2. Connect"
          fact={connection ? (
            <DotWord tone="ok" data-testid="telnyx-connected">
              {`Connected · ${connection.domain} · user ${connection.user}`}
            </DotWord>
          ) : "Makes the SIP account the line registers with"}
          verb={<Button dense variant={connection ? "secondary" : "primary"} loading={busy === "connect"}
            disabled={!keyThere || Boolean(busy)} onClick={() => void connect()} data-testid="telnyx-connect"
            title="Sends your key to Telnyx">{connection ? "Connect again" : "Connect"}</Button>} />

        {yours ? (
          <Step testId="telnyx-step-number" name="3. A number"
            fact={<DotWord tone="ok" data-testid="telnyx-yours">{`Yours: ${phoneWords(yours)} · assigned to the line`}</DotWord>} />
        ) : (
          <div className="telnyx-number" data-testid="telnyx-step-number">
            <div className="line-field">
              <span className="calls-field-line">
                <span className="telnyx-step-name">3. A number</span>
                <StringGadget label="Area code" value={area} onChange={setArea} placeholder="Area code, for example 212"
                  disabled={!connection} onKeyDown={(event) => { if (event.key === "Enter" && areaOk) void find(); }} />
                <Button dense variant="secondary" loading={busy === "find"} disabled={!connection || !areaOk || Boolean(busy)}
                  onClick={() => void find()} data-testid="telnyx-find">Find numbers</Button>
              </span>
            </div>
            {bought ? (
              <Step testId="telnyx-bought" name={phoneWords(bought)} fact="Bought · not on the line yet"
                verb={<Button dense variant="primary" loading={busy === "assign"} onClick={() => void assign(bought)}
                  data-testid="telnyx-assign">Assign</Button>} />
            ) : null}
            {numbers && !bought ? (
              numbers.length ? (
                <div className="telnyx-numbers" data-testid="telnyx-numbers">
                  {numbers.map((row) => {
                    const monthly = moneyWords(row.monthly_cost, row.currency);
                    return (
                      <div className="line-row telnyx-row" key={row.phone_number} data-testid="telnyx-number"
                        data-number={row.phone_number}>
                        <span className="line-row-name telnyx-digits">{phoneWords(row.phone_number)}</span>
                        <span className="line-row-fact telnyx-costs">
                          <Token data-testid="telnyx-monthly">{`${monthly} a month`}</Token>
                          <Token data-testid="telnyx-upfront">{`${moneyWords(row.upfront_cost, row.currency)} upfront`}</Token>
                        </span>
                        <span className="line-row-state" />
                        <span className="line-row-verb">
                          <ConfirmVerb label="Buy" variant="ghost" armedVariant="primary"
                            confirmLabel={`Buy ${phoneWords(row.phone_number)} for ${monthly} a month?`}
                            busy={busy === `buy-${row.phone_number}`} disabled={Boolean(busy) && busy !== `buy-${row.phone_number}`}
                            onConfirm={() => void buy(row)} data-testid="telnyx-buy" />
                        </span>
                      </div>
                    );
                  })}
                </div>
              ) : <p className="line-quiet" data-testid="telnyx-none">Telnyx has no number in {area.trim()} now. Try another area code.</p>
            ) : null}
          </div>
        )}

        {status?.balance ? (
          <p className="line-quiet" data-testid="telnyx-balance">
            {`Telnyx balance: ${moneyWords(status.balance.balance, status.balance.currency)}`}
          </p>
        ) : null}
        {status?.error && !failure ? <p className="calls-refusal" role="alert" data-testid="telnyx-failure">{status.error}</p> : null}
        {failure ? (
          <p className="calls-refusal" role="alert" data-testid="telnyx-failure">
            {[failure.error, failure.kept, failure.next].filter(Boolean).join(" ")}
          </p>
        ) : null}
      </div>
    </FoldGadget>
  );
}
