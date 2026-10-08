/** PHILO-14 A2 — Get Info on a drawer's object: a window of its own (board
 *  A-2, right). The GetInfo species with the facts the object has (where,
 *  from, made, due, owner, state, branch); the verbs are the object's own:
 *  Rename (in place, only where a rename path exists), Park (one press, no
 *  confirm: PHILO-13-02; only where a park path exists), Open.
 */
import { useEffect, useRef, useState } from "react";
import { Button } from "../../components/signal/Signal";
import { parkMeeting } from "../api";
import { DeskWindowFrame } from "../components/DeskWindow";
import { renameDeskObject } from "../components/InfoWindow";
import { renameLock } from "../infoContract";
import { useDesk } from "../store";
import { EditInPlace, EgressChip, GetInfo, SurfaceFooter, objectSprite } from "../surface";
import { plainFailure } from "../surface/plainFailure";
import { windowName } from "../windowName";
import { objectByRef } from "../world";
import { memberOpens, openMember } from "./open";
import { urlHost } from "./members";
import { infoWindowId, useDrawers, type OpenInfo } from "./store";
import type { GetInfoFacts } from "../surface";
import { registerProjectRepository, registrable, repositoryWords, useProjectRepository } from "../projectRepository";

/** PHILO-15 16: the Project's own Info carries its REPOSITORY (read live) and,
 *  when the Room watches a repository nobody registered, the Register verb. */
function useProjectFacts(member: OpenInfo["member"], setFailure: (text: string) => void) {
  const isProject = member.kind === "project";
  const repository = useProjectRepository(isProject ? member.id : "");
  const [busy, setBusy] = useState(false);
  if (!isProject) return { facts: member.facts, verb: null };
  const notRead = repository.failed || repository.state?.store === "not_read";
  const words = repositoryWords(repository.state, repository.failed);
  const facts: GetInfoFacts = {
    ...member.facts,
    more: [
      ...(member.facts.more ?? []),
      { key: "repository", word: "Repository", value: words },
      // Where the clone lives: the owner finds it after a refused launch.
      { key: "folder", word: "Folder", value: notRead ? "" : repository.state?.folder ?? "" },
    ],
  };
  const name = registrable(repository.state);
  const register = async () => {
    if (!name) return;
    setBusy(true);
    setFailure("");
    try {
      await registerProjectRepository(member.id, name);
      repository.reload();
    } catch (reason) {
      setFailure(plainFailure("NOT REGISTERED", reason));
    } finally {
      setBusy(false);
    }
  };
  const verb = notRead ? (
    <Button dense variant="ghost" onClick={() => repository.reload()} data-testid="info-repository-retry">
      Retry
    </Button>
  ) : name ? (
    <Button dense variant="ghost" loading={busy} onClick={() => void register()} data-testid="info-register">
      Register
    </Button>
  ) : null;
  return { facts, verb };
}

export function DrawerInfoWindow({ info }: { info: OpenInfo }) {
  const { member } = info;
  const items = useDesk((s) => s.items);
  const desk = member.renameRef ? objectByRef(items, member.renameRef) : null;
  const canRename = Boolean(desk && !renameLock(desk.kind));
  const [renaming, setRenaming] = useState(false);
  const [busy, setBusy] = useState(false);
  const [failure, setFailure] = useState("");
  const fieldRef = useRef<HTMLDivElement>(null);
  const project = useProjectFacts(member, setFailure);
  const name = desk?.title ?? member.name;
  const title = windowName({ kind: "info", name });
  const close = () => useDrawers.getState().closeInfo(member.ref);

  // Rename opens the name's editor at once (one press, not two).
  useEffect(() => {
    if (renaming) fieldRef.current?.querySelector<HTMLElement>(".surface-edit-in-place")?.click();
  }, [renaming]);

  const rename = async (next: string) => {
    setRenaming(false);
    if (!desk) return;
    setFailure("");
    try {
      await renameDeskObject(desk, next);
      useDrawers.getState().openInfo({ ...member, name: next }, info.projectId);
      useDrawers.getState().changed();
    } catch (reason) {
      setFailure(plainFailure("NOT RENAMED", reason));
    }
  };

  const park = async () => {
    const id = member.ref.slice(member.ref.indexOf(":") + 1);
    setBusy(true);
    setFailure("");
    try {
      await parkMeeting(id);
      // The receipt lands on the surviving face: the drawer, with Restore.
      useDrawers.getState().setReceipt(info.projectId, { kind: "parked", text: `PARKED · ${name}`, ids: [id] });
      close();
      useDrawers.getState().changed();
      void useDesk.getState().refresh();
    } catch (reason) {
      setFailure(plainFailure("NOT PARKED", reason));
    } finally {
      setBusy(false);
    }
  };

  return (
    <DeskWindowFrame
      id={infoWindowId(member.ref)}
      title={title}
      label={title}
      glyph="ⓘ"
      icon={<img className="drawer-winicon" src={member.sprite ?? objectSprite(member.kind, member.id)} alt="" />}
      className="desk-pullout drawer-info-window"
      minW={300}
      minH={240}
      defaultW={540}
      defaultH={460}
      open
      onClose={close}
    >
      <div className="desk-pullout-body drawer-body">
        <div className="drawer-scroll">
          {renaming ? (
            <div ref={fieldRef} className="drawer-info-rename">
              <EditInPlace value={name} label="Name" onCommit={rename} />
            </div>
          ) : null}
          <GetInfo
            id={member.id}
            kind={member.kind}
            name={name}
            kindWord={member.kindWord}
            sprite={member.sprite}
            facts={project.facts}
          />
        </div>
      </div>
      <SurfaceFooter
        egress={member.url ? <EgressChip label={urlHost(member.url)} scope="cloud" /> : null}
        receipt={failure ? <span className="drawer-receipt" data-tone="fail" role="status">{failure}</span> : null}
        verbs={
          <>
            {project.verb}
            {canRename ? (
              <Button dense variant="ghost" onClick={() => setRenaming(true)}>
                Rename
              </Button>
            ) : null}
            {member.parks ? (
              <Button dense variant="ghost" loading={busy} onClick={() => void park()}>
                Park
              </Button>
            ) : null}
            {memberOpens(member) ? (
              <Button dense variant="primary" onClick={() => openMember(member)}>
                Open
              </Button>
            ) : null}
          </>
        }
      />
    </DeskWindowFrame>
  );
}
