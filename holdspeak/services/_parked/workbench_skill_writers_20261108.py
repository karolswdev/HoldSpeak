"""PARKED 20261108 (workbench fold): what only three unreached skill routes used.

Owner ruling 2026-11-08: sequences, workflows and automation runs ARE
Programs; one implementation per concept. No live face writes a skill:
the web has no caller of POST or DELETE /api/skills, and its one PUT caller
was a parked test. (Promote to skill writes through the store itself.) Kept here,
as text, in the order it stood in ``WorkbenchService``:

- SKILL_BODY_LIMIT = 8192
- create_skill, update_skill, delete_skill.

(The unreached cancel route is parked beside its siblings; ``cancel_run``
stays: MCP ``workbench.cancel`` reaches it through ``cancel_latest_run``.)

Not imported. Restore with git revert of the parking commit.
"""
# ruff: noqa
# fmt: off
PARKED = True

'''
SKILL_BODY_LIMIT = 8192

    def create_skill(self, principal: Principal, *, title: str, body: str, **fields: Any) -> dict[str, Any]:
        if not title.strip():
            raise ValidationError("Skill title is required")
        if len(body) > SKILL_BODY_LIMIT:
            raise ValidationError(
                f"Skill body exceeds {SKILL_BODY_LIMIT:,} byte limit (got {len(body):,})"
            )
        skill = self._db.skills.upsert(
            skill_id=str(fields.get("id") or _new_id("skill")), title=title, body=body,
            source=str(fields.get("source", "owner-authored")),
            status=str(fields.get("status", "active")),
            recipe_ids=list(fields.get("recipe_ids", [])),
            created_by=str(fields.get("created_by", "")),
        )
        self._changed("skill", skill.id, "create")
        return skill.to_dict()

    def update_skill(self, principal: Principal, skill_id: str, **fields: Any) -> dict[str, Any]:
        existing = self._db.skills.get(skill_id)
        if existing is None:
            raise NotFound("skill", skill_id)

        def pick(key: str, default: Any) -> Any:
            return fields[key] if key in fields else default

        skill = self._db.skills.upsert(
            skill_id=skill_id, title=str(pick("title", existing.title)),
            body=str(pick("body", existing.body)), source=str(pick("source", existing.source)),
            status=str(pick("status", existing.status)),
            recipe_ids=list(pick("recipe_ids", existing.to_dict().get("recipe_ids", []))),
            created_by=str(pick("created_by", existing.created_by)),
        )
        self._changed("skill", skill.id, "update")
        return skill.to_dict()

    def delete_skill(self, principal: Principal, skill_id: str) -> bool:
        if not self._db.skills.delete(skill_id):
            raise NotFound("skill", skill_id)
        self._changed("skill", skill_id, "delete")
        return True

'''
