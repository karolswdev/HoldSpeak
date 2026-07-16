// HS-94-08 — delivery objects in the semantic List view. The same read model
// the Delivery board renders, expressed as an accessible table for keyboard
// and screen-reader use: a Story row opens its dossier IN a window, a Coder
// session row opens the immutable-target terminal. Renders nothing until the
// delivery read model has objects, so the plain Desk list is untouched.
import { deliveryListRows, useDelivery } from "../delivery";
import { useDeliveryDossier } from "../deliveryDossier";
import { targetHandle, useDeliveryFactory } from "../deliveryFactory";
import { useDeliveryTerminal } from "../deliveryTerminal";

export function DeliveryListSection() {
  const sources = useDelivery((s) => s.sources);
  const attempts = useDelivery((s) => s.attempts);
  const targets = useDeliveryFactory((s) => s.targets);
  const rows = deliveryListRows(sources, attempts);
  if (rows.length === 0) return null;

  const openRow = (row: (typeof rows)[number]) => {
    const ref = row.ref;
    if (ref.type === "story") {
      void useDeliveryDossier
        .getState()
        .openStory(ref.project, ref.storyId, ref.sourceId);
      return;
    }
    const target = ref.targetId
      ? targets.find((t) => t.targetId === ref.targetId)
      : null;
    if (target) useDeliveryTerminal.getState().open(targetHandle(target));
  };

  return (
    <section aria-labelledby="desk-delivery-list-title" className="desk-dlv-list">
      <h2 id="desk-delivery-list-title">Delivery work</h2>
      <div className="desk-list-scroll">
        <table
          className="desk-list-table"
          aria-labelledby="desk-delivery-list-title"
        >
          <thead>
            <tr>
              <th scope="col">Item</th>
              <th scope="col">Kind</th>
              <th scope="col">Detail</th>
              <th scope="col">Freshness</th>
            </tr>
          </thead>
          <tbody>
            {rows.map((row) => (
              <tr key={row.key}>
                <th scope="row">
                  <button
                    type="button"
                    className="desk-list-open"
                    onClick={() => openRow(row)}
                  >
                    {row.label}
                  </button>
                </th>
                <td>{row.kind}</td>
                <td>{row.detail}</td>
                <td>{row.freshness}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </section>
  );
}
