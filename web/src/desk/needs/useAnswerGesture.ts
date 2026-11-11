import { useActivationGesture } from "../../components/signal/useActivationGesture";

/** Keep the reader identity across a settled answer and the next selection. */
export const useAnswerGesture = (revision: string | null) =>
  useActivationGesture(revision, '[data-testid="needs-preview"] button');
