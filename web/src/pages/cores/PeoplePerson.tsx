/* A person has facts, one View pop-up and the kit's bounded record panes. */
import { useEffect, useState, type ReactNode } from "react";
import { InspectorBody, InspectorFacts, PaneViews } from "../../desk/surface";
import { useDesk } from "../../desk/store";
import { PeopleLedger, type PersonView } from "./PeopleLedger";
import { PersonLinks } from "./PeopleLinks";
import { dayLabel, oneOnOneWhen, relationshipLabel, type Lens, type PrepNext, type RelationshipDetail } from "./peopleModel";

export function RelationshipPane({relationship,initialLens,lensRequest,onRefresh,onProtectedFailure,onArchived,onBack,lead,issue="",retryWrite=false}:{
  relationship:RelationshipDetail;initialLens?:Lens|null;lensRequest?:{lens:Lens;seq:number}|null;
  onRefresh():void;onProtectedFailure(cause:unknown,mayHaveSaved?:boolean,kind?:"read"|"write"):void;onArchived():void;onBack?():void;lead?:ReactNode;issue?:string;retryWrite?:boolean;
}) {
  const [view,setView]=useState<PersonView>(initialLens==="info"?"links":initialLens==="history"?"brief":"ledger");
  const [composerRequest,setComposerRequest]=useState(initialLens==="context"?1:0),[next,setNext]=useState<PrepNext|null>(null);
  useEffect(()=>{if(!lensRequest)return;setView(lensRequest.lens==="info"?"links":lensRequest.lens==="history"?"brief":"ledger");if(lensRequest.lens==="context")setComposerRequest(n=>n+1);},[lensRequest]);
  const projects=useDesk(state=>state.projects);
  const facts=[relationshipLabel(relationship.relationship_kind),relationship.role_context,relationship.cadence,...projects.filter(project=>relationship.project_refs?.includes(project.id)).map(project=>project.name)].filter(Boolean).join(" · ");
  return <InspectorBody>
    <InspectorFacts name="Person facts" header={false} testId="people-detail-head" data-feedback-redact="true" rows={[
      {label:"Relationship",value:<span data-testid="people-who-meta">{facts}</span>},
      {label:"Next 1:1",value:next?.at||relationship.next_one_on_one?<span data-testid="people-next-1on1">{oneOnOneWhen((next?.at??relationship.next_one_on_one)!)}</span>:""},
      {label:"Last 1:1",value:next?.last?dayLabel(next.last):""},
    ]}/>
    <PaneViews label="Person view" value={view} onChange={value=>setView(value as PersonView)} tabs={[{id:"ledger",label:"Ledger"},{id:"links",label:"Links"},{id:"brief",label:"1:1 brief"},{id:"agenda",label:"Agenda"}]}>
      <PeopleLedger key={relationship.id} relationship={relationship} onRefresh={onRefresh} onProtectedFailure={onProtectedFailure} onNext={setNext} composerRequest={composerRequest} view={view} issue={issue} retryWrite={retryWrite}
        links={<PersonLinks relationship={relationship} onRefresh={onRefresh} onProtectedFailure={onProtectedFailure} onArchived={onArchived}/>}/>
    </PaneViews>
  </InspectorBody>;
}
