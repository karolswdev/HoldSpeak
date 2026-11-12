import { Button } from "../../components/signal/Signal";
import { useEffect } from "react";
import { CycleGadget } from "../surface";
import { loadPeople, useScreenMembersStore } from "../screen/members";
export interface PersonChoice { id: string; name: string }
export const NOBODY = "Nobody yet";
export function PersonPicker({ value, onPick, disabled, "data-testid": testId }: {
  value: PersonChoice | null; onPick(choice: PersonChoice | null): void;
  disabled?: boolean; "data-testid"?: string;
}) {
  const people = useScreenMembersStore(state => state.people);
  useEffect(() => { void loadPeople(); }, []);
  const persons = people?.state === "ready" ? people.persons : [];
  return <span data-testid={testId}><CycleGadget label="Person" roster value={value?.id ?? ""} disabled={disabled}
    options={[{value:"",label:NOBODY}, ...(value && !persons.some(row => row.id === value.id) ? [{value:value.id,label:value.name}] : []),
      ...persons.map(person => ({value:person.id,label:person.name})),
      ...(people?.state === "failed" ? [{value:"failed",label:"People did not load",disabled:true}] : [])]}
    onChange={id => onPick(persons.find(row => row.id === id) ?? null)} />{people?.state === "failed" ? <Button dense variant="secondary" onClick={() => void loadPeople()}>Retry people</Button> : null}</span>;
}
