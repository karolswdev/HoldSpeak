HS-125-06 and HS-125-07 are tightly coupled: both modify FollowThroughService
in follow_through_service.py. Story 06 refines lane assignment logic (due/stall
semantics) and story 07 adds completion verbs that depend on the refined states.
Splitting would require an artificial intermediate commit.
