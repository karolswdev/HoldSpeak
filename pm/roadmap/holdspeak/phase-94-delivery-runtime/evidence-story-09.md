# Evidence - HS-94-09

- **Story:** HS-94-09 - Native parity and tailnet HTTPS onboarding
- **Status:** done
- **Date:** 2026-07-16

## Proof

### Captured run — 2026-07-16T09:02:07Z

- **Command:** `swift test --package-path apple`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** 53f44ae79b3fd52c3aa4a80f7f577a8fd6c6e2f2

```text
[0/1] Planning build
Building for debugging...
[0/2] Write swift-version-39B54973F684ADAB.txt
Build complete! (0.53s)
Test Suite 'All tests' started at 2026-07-16 03:02:09.245.
Test Suite 'HoldSpeakMobilePackageTests.xctest' started at 2026-07-16 03:02:09.246.
Test Suite 'ADRCandidatesTests' started at 2026-07-16 03:02:09.246.
Test Case '-[RuntimeCoreTests.ADRCandidatesTests testADRCandidatesValidate]' started.
Test Case '-[RuntimeCoreTests.ADRCandidatesTests testADRCandidatesValidate]' passed (0.003 seconds).
Test Case '-[RuntimeCoreTests.ADRCandidatesTests testADRDoesNotFabricate]' started.
Test Case '-[RuntimeCoreTests.ADRCandidatesTests testADRDoesNotFabricate]' passed (0.000 seconds).
Test Suite 'ADRCandidatesTests' passed at 2026-07-16 03:02:09.250.
	 Executed 2 tests, with 0 failures (0 unexpected) in 0.004 (0.004) seconds
Test Suite 'ActivityClientTests' started at 2026-07-16 03:02:09.250.
Test Case '-[ProvidersTests.ActivityClientTests testActivityNudgeContractDecodesEveryServerField]' started.
Test Case '-[ProvidersTests.ActivityClientTests testActivityNudgeContractDecodesEveryServerField]' passed (0.000 seconds).
Test Case '-[ProvidersTests.ActivityClientTests testActivityNudgesDecodeServerShapeWithCitations]' started.
Test Case '-[ProvidersTests.ActivityClientTests testActivityNudgesDecodeServerShapeWithCitations]' passed (0.006 seconds).
Test Case '-[ProvidersTests.ActivityClientTests testActivityNudgesEmptyWhenTrackingOff]' started.
Test Case '-[ProvidersTests.ActivityClientTests testActivityNudgesEmptyWhenTrackingOff]' passed (0.001 seconds).
Test Case '-[ProvidersTests.ActivityClientTests testActivityNudgesHTTPErrorThrows]' started.
Test Case '-[ProvidersTests.ActivityClientTests testActivityNudgesHTTPErrorThrows]' passed (0.000 seconds).
Test Case '-[ProvidersTests.ActivityClientTests testBriefingDecodesDigest]' started.
Test Case '-[ProvidersTests.ActivityClientTests testBriefingDecodesDigest]' passed (0.001 seconds).
Test Case '-[ProvidersTests.ActivityClientTests testBriefingNilWhenAbsent]' started.
Test Case '-[ProvidersTests.ActivityClientTests testBriefingNilWhenAbsent]' passed (0.000 seconds).
Test Case '-[ProvidersTests.ActivityClientTests testDismissNudgeHitsKeyedPath]' started.
Test Case '-[ProvidersTests.ActivityClientTests testDismissNudgeHitsKeyedPath]' passed (0.000 seconds).
Test Case '-[ProvidersTests.ActivityClientTests testSelectNudgePostsRealIntRecordId]' started.
Test Case '-[ProvidersTests.ActivityClientTests testSelectNudgePostsRealIntRecordId]' passed (0.000 seconds).
Test Case '-[ProvidersTests.ActivityClientTests testSelectNudgeUnknownIdThrows]' started.
Test Case '-[ProvidersTests.ActivityClientTests testSelectNudgeUnknownIdThrows]' passed (0.000 seconds).
Test Suite 'ActivityClientTests' passed at 2026-07-16 03:02:09.260.
	 Executed 9 tests, with 0 failures (0 unexpected) in 0.009 (0.010) seconds
Test Suite 'AftercareClientTests' started at 2026-07-16 03:02:09.260.
Test Case '-[ProvidersTests.AftercareClientTests testAftercare404Throws]' started.
Test Case '-[ProvidersTests.AftercareClientTests testAftercare404Throws]' passed (0.000 seconds).
Test Case '-[ProvidersTests.AftercareClientTests testAftercareClientGETsAndDecodes]' started.
Test Case '-[ProvidersTests.AftercareClientTests testAftercareClientGETsAndDecodes]' passed (0.001 seconds).
Test Case '-[ProvidersTests.AftercareClientTests testAftercareDigestDecodesFaithfully]' started.
Test Case '-[ProvidersTests.AftercareClientTests testAftercareDigestDecodesFaithfully]' passed (0.000 seconds).
Test Case '-[ProvidersTests.AftercareClientTests testEmptyDigestDecodes]' started.
Test Case '-[ProvidersTests.AftercareClientTests testEmptyDigestDecodes]' passed (0.000 seconds).
Test Case '-[ProvidersTests.AftercareClientTests testFileAftercareIssue400Throws]' started.
Test Case '-[ProvidersTests.AftercareClientTests testFileAftercareIssue400Throws]' passed (0.000 seconds).
Test Case '-[ProvidersTests.AftercareClientTests testFileAftercareIssueErrorEnvelopeDecodesOn400]' started.
Test Case '-[ProvidersTests.AftercareClientTests testFileAftercareIssueErrorEnvelopeDecodesOn400]' passed (0.000 seconds).
Test Case '-[ProvidersTests.AftercareClientTests testFileAftercareIssuePostsAndDecodesProposal]' started.
Test Case '-[ProvidersTests.AftercareClientTests testFileAftercareIssuePostsAndDecodesProposal]' passed (0.001 seconds).
Test Suite 'AftercareClientTests' passed at 2026-07-16 03:02:09.264.
	 Executed 7 tests, with 0 failures (0 unexpected) in 0.004 (0.004) seconds
Test Suite 'ArtifactCorrectionTests' started at 2026-07-16 03:02:09.264.
Test Case '-[RuntimeCoreTests.ArtifactCorrectionTests testCorrectedProducesSameTypeDraftWithVoiceProvenance]' started.
Test Case '-[RuntimeCoreTests.ArtifactCorrectionTests testCorrectedProducesSameTypeDraftWithVoiceProvenance]' passed (0.000 seconds).
Test Case '-[RuntimeCoreTests.ArtifactCorrectionTests testPromptFusesOriginalCorrectionAndTranscript]' started.
Test Case '-[RuntimeCoreTests.ArtifactCorrectionTests testPromptFusesOriginalCorrectionAndTranscript]' passed (0.000 seconds).
Test Suite 'ArtifactCorrectionTests' passed at 2026-07-16 03:02:09.265.
	 Executed 2 tests, with 0 failures (0 unexpected) in 0.001 (0.001) seconds
Test Suite 'ArtifactGenerationEngineTests' started at 2026-07-16 03:02:09.265.
Test Case '-[RuntimeCoreTests.ArtifactGenerationEngineTests testBatchIsResilientPerType]' started.
Test Case '-[RuntimeCoreTests.ArtifactGenerationEngineTests testBatchIsResilientPerType]' passed (0.000 seconds).
Test Case '-[RuntimeCoreTests.ArtifactGenerationEngineTests testEmitsSchemaValidArtifact]' started.
Test Case '-[RuntimeCoreTests.ArtifactGenerationEngineTests testEmitsSchemaValidArtifact]' passed (0.000 seconds).
Test Case '-[RuntimeCoreTests.ArtifactGenerationEngineTests testMalformedOutputIsRecoverable]' started.
Test Case '-[RuntimeCoreTests.ArtifactGenerationEngineTests testMalformedOutputIsRecoverable]' passed (0.000 seconds).
Test Case '-[RuntimeCoreTests.ArtifactGenerationEngineTests testNeverAutoAccepts]' started.
Test Case '-[RuntimeCoreTests.ArtifactGenerationEngineTests testNeverAutoAccepts]' passed (0.000 seconds).
Test Suite 'ArtifactGenerationEngineTests' passed at 2026-07-16 03:02:09.267.
	 Executed 4 tests, with 0 failures (0 unexpected) in 0.001 (0.002) seconds
Test Suite 'ArtifactsClientTests' started at 2026-07-16 03:02:09.267.
Test Case '-[ProvidersTests.ArtifactsClientTests testConfidenceIsOptionalAndEmptySourcesDecode]' started.
Test Case '-[ProvidersTests.ArtifactsClientTests testConfidenceIsOptionalAndEmptySourcesDecode]' passed (0.000 seconds).
Test Case '-[ProvidersTests.ArtifactsClientTests testDecodesEnvelopeWithConfidenceAndSources]' started.
Test Case '-[ProvidersTests.ArtifactsClientTests testDecodesEnvelopeWithConfidenceAndSources]' passed (0.000 seconds).
Test Suite 'ArtifactsClientTests' passed at 2026-07-16 03:02:09.268.
	 Executed 2 tests, with 0 failures (0 unexpected) in 0.001 (0.001) seconds
Test Suite 'AskClientTests' started at 2026-07-16 03:02:09.268.
Test Case '-[ProvidersTests.AskClientTests testLocalRunDecodesWithoutHost]' started.
Test Case '-[ProvidersTests.AskClientTests testLocalRunDecodesWithoutHost]' passed (0.001 seconds).
Test Case '-[ProvidersTests.AskClientTests testNon2xxThrows]' started.
Test Case '-[ProvidersTests.AskClientTests testNon2xxThrows]' passed (0.001 seconds).
Test Case '-[ProvidersTests.AskClientTests testRunStepPostsThePromptAndDecodesTheHonestEgress]' started.
Test Case '-[ProvidersTests.AskClientTests testRunStepPostsThePromptAndDecodesTheHonestEgress]' passed (0.000 seconds).
Test Suite 'AskClientTests' passed at 2026-07-16 03:02:09.270.
	 Executed 3 tests, with 0 failures (0 unexpected) in 0.002 (0.002) seconds
Test Suite 'AudioTests' started at 2026-07-16 03:02:09.270.
Test Case '-[ProvidersTests.AudioTests testAccumulatorIsBoundedAndCountsDrops]' started.
Test Case '-[ProvidersTests.AudioTests testAccumulatorIsBoundedAndCountsDrops]' passed (0.000 seconds).
Test Case '-[ProvidersTests.AudioTests testCaptureToWavPipeline]' started.
Test Case '-[ProvidersTests.AudioTests testCaptureToWavPipeline]' passed (0.000 seconds).
Test Case '-[ProvidersTests.AudioTests testWavHeaderIs16kMonoPCM16]' started.
Test Case '-[ProvidersTests.AudioTests testWavHeaderIs16kMonoPCM16]' passed (0.000 seconds).
Test Suite 'AudioTests' passed at 2026-07-16 03:02:09.270.
	 Executed 3 tests, with 0 failures (0 unexpected) in 0.000 (0.001) seconds
Test Suite 'AuthorityClientTests' started at 2026-07-16 03:02:09.270.
Test Case '-[ProvidersTests.AuthorityClientTests testAuthorityPolicyDecodesTheSharedVersionedPosture]' started.
Test Case '-[ProvidersTests.AuthorityClientTests testAuthorityPolicyDecodesTheSharedVersionedPosture]' passed (0.001 seconds).
Test Suite 'AuthorityClientTests' passed at 2026-07-16 03:02:09.271.
	 Executed 1 test, with 0 failures (0 unexpected) in 0.001 (0.001) seconds
Test Suite 'BlueprintInterpreterTests' started at 2026-07-16 03:02:09.271.
Test Case '-[RuntimeCoreTests.BlueprintInterpreterTests testAsyncStreamSurfaceYieldsEvents]' started.
Test Case '-[RuntimeCoreTests.BlueprintInterpreterTests testAsyncStreamSurfaceYieldsEvents]' passed (0.001 seconds).
Test Case '-[RuntimeCoreTests.BlueprintInterpreterTests testBlueprintAndEventsAreCodable]' started.
Test Case '-[RuntimeCoreTests.BlueprintInterpreterTests testBlueprintAndEventsAreCodable]' passed (0.003 seconds).
Test Case '-[RuntimeCoreTests.BlueprintInterpreterTests testBranchTakesFalsePathWhenConditionFails]' started.
Test Case '-[RuntimeCoreTests.BlueprintInterpreterTests testBranchTakesFalsePathWhenConditionFails]' passed (0.000 seconds).
Test Case '-[RuntimeCoreTests.BlueprintInterpreterTests testBranchTakesTruePathWhenConditionHolds]' started.
Test Case '-[RuntimeCoreTests.BlueprintInterpreterTests testBranchTakesTruePathWhenConditionHolds]' passed (0.000 seconds).
Test Case '-[RuntimeCoreTests.BlueprintInterpreterTests testDataResolutionPullsUpstreamValueAndSubstitutesInput]' started.
Test Case '-[RuntimeCoreTests.BlueprintInterpreterTests testDataResolutionPullsUpstreamValueAndSubstitutesInput]' passed (0.000 seconds).
Test Case '-[RuntimeCoreTests.BlueprintInterpreterTests testExecutionEventStreamEmitsExpectedOrderedSequence]' started.
Test Case '-[RuntimeCoreTests.BlueprintInterpreterTests testExecutionEventStreamEmitsExpectedOrderedSequence]' passed (0.000 seconds).
Test Case '-[RuntimeCoreTests.BlueprintInterpreterTests testForEachRunsBodyExactlyNTimes]' started.
Test Case '-[RuntimeCoreTests.BlueprintInterpreterTests testForEachRunsBodyExactlyNTimes]' passed (0.000 seconds).
Test Case '-[RuntimeCoreTests.BlueprintInterpreterTests testModelFailureFallbackPolicyRecovers]' started.
Test Case '-[RuntimeCoreTests.BlueprintInterpreterTests testModelFailureFallbackPolicyRecovers]' passed (0.000 seconds).
Test Case '-[RuntimeCoreTests.BlueprintInterpreterTests testModelFailureRetriesThenFailsWithoutCrash]' started.
Test Case '-[RuntimeCoreTests.BlueprintInterpreterTests testModelFailureRetriesThenFailsWithoutCrash]' passed (0.000 seconds).
Test Case '-[RuntimeCoreTests.BlueprintInterpreterTests testModelFailureSkipPolicyCarriesInput]' started.
Test Case '-[RuntimeCoreTests.BlueprintInterpreterTests testModelFailureSkipPolicyCarriesInput]' passed (0.000 seconds).
Test Case '-[RuntimeCoreTests.BlueprintInterpreterTests testValidationRejectsDataTypeMismatch]' started.
Test Case '-[RuntimeCoreTests.BlueprintInterpreterTests testValidationRejectsDataTypeMismatch]' passed (0.000 seconds).
Test Case '-[RuntimeCoreTests.BlueprintInterpreterTests testWhileLoopIsBoundedByMaxIterations]' started.
Test Case '-[RuntimeCoreTests.BlueprintInterpreterTests testWhileLoopIsBoundedByMaxIterations]' passed (0.000 seconds).
Test Case '-[RuntimeCoreTests.BlueprintInterpreterTests testWhileLoopStopsWhenConditionFails]' started.
Test Case '-[RuntimeCoreTests.BlueprintInterpreterTests testWhileLoopStopsWhenConditionFails]' passed (0.000 seconds).
Test Suite 'BlueprintInterpreterTests' passed at 2026-07-16 03:02:09.278.
	 Executed 13 tests, with 0 failures (0 unexpected) in 0.006 (0.007) seconds
Test Suite 'BlueprintWireTests' started at 2026-07-16 03:02:09.278.
Test Case '-[RuntimeCoreTests.BlueprintWireTests testBranchingBlueprintMatchesTheGoldenFixture]' started.
Test Case '-[RuntimeCoreTests.BlueprintWireTests testBranchingBlueprintMatchesTheGoldenFixture]' passed (0.001 seconds).
Test Case '-[RuntimeCoreTests.BlueprintWireTests testGraphJSONValueRoundTripsIntoWorkflowDefinition]' started.
Test Case '-[RuntimeCoreTests.BlueprintWireTests testGraphJSONValueRoundTripsIntoWorkflowDefinition]' passed (0.002 seconds).
Test Case '-[RuntimeCoreTests.BlueprintWireTests testLinearBlueprintMatchesTheGoldenFixture]' started.
Test Case '-[RuntimeCoreTests.BlueprintWireTests testLinearBlueprintMatchesTheGoldenFixture]' passed (0.000 seconds).
Test Case '-[RuntimeCoreTests.BlueprintWireTests testRunsOnAbsentStaysAbsentOnTheWire]' started.
Test Case '-[RuntimeCoreTests.BlueprintWireTests testRunsOnAbsentStaysAbsentOnTheWire]' passed (0.000 seconds).
Test Case '-[RuntimeCoreTests.BlueprintWireTests testWireShapeIsTheHubContract]' started.
Test Case '-[RuntimeCoreTests.BlueprintWireTests testWireShapeIsTheHubContract]' passed (0.000 seconds).
Test Suite 'BlueprintWireTests' passed at 2026-07-16 03:02:09.282.
	 Executed 5 tests, with 0 failures (0 unexpected) in 0.004 (0.004) seconds
Test Suite 'BubblePlacementTests' started at 2026-07-16 03:02:09.282.
Test Case '-[RuntimeCoreTests.BubblePlacementTests testDropBackInTheStreamSnapsBack]' started.
Test Case '-[RuntimeCoreTests.BubblePlacementTests testDropBackInTheStreamSnapsBack]' passed (0.000 seconds).
Test Case '-[RuntimeCoreTests.BubblePlacementTests testDropBelowTheStreamIsLoose]' started.
Test Case '-[RuntimeCoreTests.BubblePlacementTests testDropBelowTheStreamIsLoose]' passed (0.000 seconds).
Test Case '-[RuntimeCoreTests.BubblePlacementTests testDropOnTackZoneTacks]' started.
Test Case '-[RuntimeCoreTests.BubblePlacementTests testDropOnTackZoneTacks]' passed (0.000 seconds).
Test Case '-[RuntimeCoreTests.BubblePlacementTests testPlainPlacementIsTheDefaultBelowTheFold]' started.
Test Case '-[RuntimeCoreTests.BubblePlacementTests testPlainPlacementIsTheDefaultBelowTheFold]' passed (0.000 seconds).
Test Case '-[RuntimeCoreTests.BubblePlacementTests testTackZoneWinsEvenAboveThePinFloor]' started.
Test Case '-[RuntimeCoreTests.BubblePlacementTests testTackZoneWinsEvenAboveThePinFloor]' passed (0.000 seconds).
Test Suite 'BubblePlacementTests' passed at 2026-07-16 03:02:09.283.
	 Executed 5 tests, with 0 failures (0 unexpected) in 0.001 (0.001) seconds
Test Suite 'CardLayoutTests' started at 2026-07-16 03:02:09.283.
Test Case '-[RuntimeCoreTests.CardLayoutTests testClampWidthHoldsTheReadableRange]' started.
Test Case '-[RuntimeCoreTests.CardLayoutTests testClampWidthHoldsTheReadableRange]' passed (0.000 seconds).
Test Case '-[RuntimeCoreTests.CardLayoutTests testTidyCentersEachRow]' started.
Test Case '-[RuntimeCoreTests.CardLayoutTests testTidyCentersEachRow]' passed (0.000 seconds).
Test Case '-[RuntimeCoreTests.CardLayoutTests testTidyEmptyIsEmpty]' started.
Test Case '-[RuntimeCoreTests.CardLayoutTests testTidyEmptyIsEmpty]' passed (0.000 seconds).
Test Case '-[RuntimeCoreTests.CardLayoutTests testTidyFlowsIntoRows]' started.
Test Case '-[RuntimeCoreTests.CardLayoutTests testTidyFlowsIntoRows]' passed (0.000 seconds).
Test Case '-[RuntimeCoreTests.CardLayoutTests testTidyPlacesEveryCardBelowTheStreamAndOnScreen]' started.
Test Case '-[RuntimeCoreTests.CardLayoutTests testTidyPlacesEveryCardBelowTheStreamAndOnScreen]' passed (0.000 seconds).
Test Suite 'CardLayoutTests' passed at 2026-07-16 03:02:09.284.
	 Executed 5 tests, with 0 failures (0 unexpected) in 0.001 (0.001) seconds
Test Suite 'ChangeSetToleranceTests' started at 2026-07-16 03:02:09.284.
Test Case '-[ContractsTests.ChangeSetToleranceTests testANovelTypeDropsOneRecordNotTheWholeSet]' started.
Test Case '-[ContractsTests.ChangeSetToleranceTests testANovelTypeDropsOneRecordNotTheWholeSet]' passed (0.001 seconds).
Test Case '-[ContractsTests.ChangeSetToleranceTests testCleanSetsReportZeroUndecoded]' started.
Test Case '-[ContractsTests.ChangeSetToleranceTests testCleanSetsReportZeroUndecoded]' passed (0.002 seconds).
Test Case '-[ContractsTests.ChangeSetToleranceTests testRunOutputIsAKnownArtifactType]' started.
Test Case '-[ContractsTests.ChangeSetToleranceTests testRunOutputIsAKnownArtifactType]' passed (0.000 seconds).
Test Suite 'ChangeSetToleranceTests' passed at 2026-07-16 03:02:09.287.
	 Executed 3 tests, with 0 failures (0 unexpected) in 0.003 (0.003) seconds
Test Suite 'ChunkedExtractionTests' started at 2026-07-16 03:02:09.287.
Test Case '-[RuntimeCoreTests.ChunkedExtractionTests testBudgetIsMonotonicInRAM]' started.
Test Case '-[RuntimeCoreTests.ChunkedExtractionTests testBudgetIsMonotonicInRAM]' passed (0.000 seconds).
Test Case '-[RuntimeCoreTests.ChunkedExtractionTests testBudgetReturnsCeilingWhenRAMIsAmple]' started.
Test Case '-[RuntimeCoreTests.ChunkedExtractionTests testBudgetReturnsCeilingWhenRAMIsAmple]' passed (0.000 seconds).
Test Case '-[RuntimeCoreTests.ChunkedExtractionTests testBudgetShrinksOnConstrainedDeviceAndNeverExceedsRAM]' started.
Test Case '-[RuntimeCoreTests.ChunkedExtractionTests testBudgetShrinksOnConstrainedDeviceAndNeverExceedsRAM]' passed (0.000 seconds).
Test Case '-[RuntimeCoreTests.ChunkedExtractionTests testChunkedExtractionWindowsThenMergesAcrossWindows]' started.
Test Case '-[RuntimeCoreTests.ChunkedExtractionTests testChunkedExtractionWindowsThenMergesAcrossWindows]' passed (0.001 seconds).
Test Case '-[RuntimeCoreTests.ChunkedExtractionTests testDedupCollapsesCrossWindowDuplicatesKeepingHigherConfidence]' started.
Test Case '-[RuntimeCoreTests.ChunkedExtractionTests testDedupCollapsesCrossWindowDuplicatesKeepingHigherConfidence]' passed (0.000 seconds).
Test Case '-[RuntimeCoreTests.ChunkedExtractionTests testDedupKeepsDifferentTypesSeparate]' started.
Test Case '-[RuntimeCoreTests.ChunkedExtractionTests testDedupKeepsDifferentTypesSeparate]' passed (0.000 seconds).
Test Case '-[RuntimeCoreTests.ChunkedExtractionTests testEmptyTranscriptYieldsNoWindows]' started.
Test Case '-[RuntimeCoreTests.ChunkedExtractionTests testEmptyTranscriptYieldsNoWindows]' passed (0.000 seconds).
Test Case '-[RuntimeCoreTests.ChunkedExtractionTests testNeedsChunkingThreshold]' started.
Test Case '-[RuntimeCoreTests.ChunkedExtractionTests testNeedsChunkingThreshold]' passed (0.000 seconds).
Test Case '-[RuntimeCoreTests.ChunkedExtractionTests testOversizedSegmentIsSplitSoEveryWindowFitsBudget]' started.
Test Case '-[RuntimeCoreTests.ChunkedExtractionTests testOversizedSegmentIsSplitSoEveryWindowFitsBudget]' passed (0.000 seconds).
Test Case '-[RuntimeCoreTests.ChunkedExtractionTests testShortTranscriptDoesNotChunk]' started.
Test Case '-[RuntimeCoreTests.ChunkedExtractionTests testShortTranscriptDoesNotChunk]' passed (0.000 seconds).
Test Case '-[RuntimeCoreTests.ChunkedExtractionTests testSplitOversizedInterpolatesTimingMonotonically]' started.
Test Case '-[RuntimeCoreTests.ChunkedExtractionTests testSplitOversizedInterpolatesTimingMonotonically]' passed (0.000 seconds).
Test Case '-[RuntimeCoreTests.ChunkedExtractionTests testSplitTextHardCutsAnUnbrokenSpan]' started.
Test Case '-[RuntimeCoreTests.ChunkedExtractionTests testSplitTextHardCutsAnUnbrokenSpan]' passed (0.000 seconds).
Test Case '-[RuntimeCoreTests.ChunkedExtractionTests testSplitTextPrefersSentenceBoundaries]' started.
Test Case '-[RuntimeCoreTests.ChunkedExtractionTests testSplitTextPrefersSentenceBoundaries]' passed (0.000 seconds).
Test Case '-[RuntimeCoreTests.ChunkedExtractionTests testWindowReservesPromptAndOutput]' started.
Test Case '-[RuntimeCoreTests.ChunkedExtractionTests testWindowReservesPromptAndOutput]' passed (0.000 seconds).
Test Case '-[RuntimeCoreTests.ChunkedExtr
[PMO_EVIDENCE_OUTPUT_TRUNCATED]
```
