/* Settings ▸ Calls ▸ Telnyx: the write-only key stays available to replace.
 * Connect shows until the SIP account exists. Available numbers use the
 * shared selection list, with monthly and upfront costs. Buy opens an
 * in-window question; only confirmation sends the saved quote to the hub.
 * The hub then assigns the number to the line. A failed assignment keeps
 * Assign available without buying the number again. */
import { useCallback, useEffect, useState, type ReactNode } from "react";
import { Button } from "../../components/signal/Signal";
import { StringGadget } from "../surface/gadgets";
import { ListView, PaneActions, PreferencePane, GadgetRow } from "../surface";
import { DotWord } from "../surface/kit";
import { assignTelnyxNumber, buyTelnyxNumber, connectTelnyx, findTelnyxNumbers, readTelnyxStatus, telnyxRefusal } from "./api";
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
  return <div data-testid={testId}><GadgetRow label={name} fact={fact}>{verb ?? <span />}</GadgetRow></div>;
}

export function TelnyxSetup({ keyRow, onChanged }: { keyRow: ReactNode; onChanged?(): void | Promise<void> }) {
  const [status, setStatus] = useState<TelnyxStatus | null>(null);
  const [busy, setBusy] = useState("");
  const [failure, setFailure] = useState<TelnyxRefusal | null>(null);
  const [area, setArea] = useState("");
  const [numbers, setNumbers] = useState<TelnyxNumber[] | null>(null);
  const [bought, setBought] = useState("");
  const [askBuy, setAskBuy] = useState<TelnyxNumber | null>(null);

  const load = useCallback(async () => {
    try { setStatus(await readTelnyxStatus()); } catch (error) { setFailure(telnyxRefusal(error)); }
  }, []);
  useEffect(() => {
    void load();
  }, [load]);

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
  const assign = (number: string) =>
    press("assign", async () => {
      await assignTelnyxNumber(number);
      setBought("");
      setAskBuy(null);
      setNumbers(null);
      await load();
      await onChanged?.();
    });
  const buy = (row: TelnyxNumber) =>
    press(`buy-${row.phone_number}`, async () => {
      await buyTelnyxNumber(row);
      setBought(row.phone_number);
      await assignTelnyxNumber(row.phone_number);
      setBought("");
      setAskBuy(null);
      setNumbers(null);
      await load();
      await onChanged?.();
    });

  const keyThere = Boolean(status && status.key !== "missing");
  const connection = status?.connection ?? null;
  const yours = status?.number ?? "";
  const areaOk = /^\d{3}$/.test(area.trim());

  return (
    <PreferencePane label="Telnyx">
      <div className="surface-preference-pane" data-testid="telnyx-setup" data-done={yours ? "" : undefined}>
        <div className="surface-pane-group" data-testid="telnyx-step-key">
          {keyRow}
        </div>

        {!connection ? (
          <Step
            testId="telnyx-step-connect"
            name="Connect"
            verb={
              <Button
                dense
                variant="primary"
                loading={busy === "connect"}
                disabled={!keyThere || Boolean(busy)}
                onClick={() => void connect()}
                data-testid="telnyx-connect"
                title="Sends your key to Telnyx"
              >
                Connect
              </Button>
            }
          />
        ) : null}

        {yours ? (
          <Step
            testId="telnyx-step-number"
            name="Number"
            fact={<DotWord tone="ok" data-testid="telnyx-yours">{`Yours: ${phoneWords(yours)} · assigned to the line`}</DotWord>}
          />
        ) : connection ? (
          <div className="surface-tab-panel" data-testid="telnyx-step-number">
            <div className="line-field">
              <span className="calls-field-line">
                <StringGadget
                  label="Area code"
                  value={area}
                  onChange={setArea}
                  placeholder="Area code, for example 212"
                  disabled={!connection}
                  onKeyDown={(event) => {
                    if (event.key === "Enter" && areaOk) void find();
                  }}
                />
                <Button
                  dense
                  variant="secondary"
                  loading={busy === "find"}
                  disabled={!connection || !areaOk || Boolean(busy)}
                  onClick={() => void find()}
                  data-testid="telnyx-find"
                >
                  Find numbers
                </Button>
              </span>
            </div>
            {bought ? (
              <Step
                testId="telnyx-bought"
                name={phoneWords(bought)}
                fact="Bought · not on the line yet"
                verb={
                  <Button dense variant="primary" loading={busy === "assign"} onClick={() => void assign(bought)} data-testid="telnyx-assign">
                    Assign
                  </Button>
                }
              />
            ) : null}
            {numbers && !bought ? (
              numbers.length ? (
                <div className="surface-tab-panel" data-testid="telnyx-numbers">
                  <ListView
                    label="Available numbers"
                    rows={numbers.map((row) => ({
                      id: row.phone_number,
                      kind: "number",
                      name: phoneWords(row.phone_number),
                      cells: {
                        monthly: <span data-testid="telnyx-monthly">{`${moneyWords(row.monthly_cost, row.currency)} a month`}</span>,
                        upfront: <span data-testid="telnyx-upfront">{`${moneyWords(row.upfront_cost, row.currency)} upfront`}</span>,
                      },
                    }))}
                    columns={[
                      { key: "name", word: "Number", priority: 100 },
                      { key: "monthly", word: "Monthly", priority: 30 },
                      { key: "upfront", word: "Upfront", priority: 10 },
                    ]}
                    defaultVerb="buy"
                    onSelect={() => setAskBuy(null)}
                    rowProps={(row) => ({
                      "data-testid": "telnyx-number",
                      "data-number": row.id,
                    })}
                    verbs={[
                      {
                        id: "buy",
                        label: "Buy…",
                        key: "Enter",
                        enabled: (row) => Boolean(row) && !busy,
                        run: (row) => setAskBuy(numbers.find((number) => number.phone_number === row!.id) ?? null),
                      },
                    ]}
                  />
                  {askBuy ? (
                    <PaneActions role="group" aria-label={`Buy ${phoneWords(askBuy.phone_number)}?`}>
                      <span>{`Buy ${phoneWords(askBuy.phone_number)} for ${moneyWords(askBuy.monthly_cost, askBuy.currency)} a month and ${moneyWords(askBuy.upfront_cost, askBuy.currency)} upfront?`}</span>
                      <Button dense variant="ghost" disabled={Boolean(busy)} onClick={() => setAskBuy(null)}>
                        Cancel
                      </Button>
                      <Button
                        dense
                        variant="primary"
                        loading={busy === `buy-${askBuy.phone_number}`}
                        disabled={Boolean(busy)}
                        onClick={() => void buy(askBuy)}
                        data-testid="telnyx-buy"
                      >
                        Buy
                      </Button>
                    </PaneActions>
                  ) : null}
                </div>
              ) : (
                <p className="line-quiet" data-testid="telnyx-none">
                  Telnyx has no number in {area.trim()} now. Try another area code.
                </p>
              )
            ) : null}
          </div>
        ) : null}

        {status?.balance ? (
          <p className="line-quiet" data-testid="telnyx-balance">
            {`Telnyx balance: ${moneyWords(status.balance.balance, status.balance.currency)}`}
          </p>
        ) : null}
        {status?.error && !failure ? (
          <p className="calls-refusal" role="alert" data-testid="telnyx-failure">
            {status.error}
          </p>
        ) : null}
        {failure ? (
          <p className="calls-refusal" role="alert" data-testid="telnyx-failure">
            {[failure.error, failure.kept, failure.next].filter(Boolean).join(" ")}
          </p>
        ) : null}
      </div>
    </PreferencePane>
  );
}
