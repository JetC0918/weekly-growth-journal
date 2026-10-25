export const PROMPTS = [
  { id: "wentWell", label: "What went well this week?" },
  { id: "didntGoWell", label: "What didn't go well?" },
  { id: "handledBetter", label: "What could I have handled better?" },
  { id: "learned", label: "What did I learn about myself?" },
  { id: "doDifferently", label: "What should I do differently next week?" },
] as const;

export type PromptId = (typeof PROMPTS)[number]["id"];
export type Answers = Record<PromptId, string>;

export interface FollowUp {
  question: string;
  answer: string;
}

export interface PreviousActionCheck {
  commitmentId: string;
  attempted: "yes" | "partly" | "no" | "";
  whatHappened: string;
  learned: string;
}

export interface Review {
  id: string;
  /** Monday of the reviewed week, YYYY-MM-DD */
  weekStart: string;
  answers: Answers;
  freeWriting: string;
  followUps: FollowUp[];
  previousAction?: PreviousActionCheck | undefined;
  status: "draft" | "completed";
  createdAt: string;
  updatedAt: string;
}

export type InsightKind = "observation" | "hypothesis";
export type InsightStatus = "pending" | "accepted" | "rejected";

export interface Insight {
  id: string;
  text: string;
  kind: InsightKind;
  /** What the user actually wrote that supports this */
  evidence: string;
  status: InsightStatus;
  correction?: string;
}

export interface Report {
  id: string;
  reviewId: string;
  takeaways: Insight[];
  strengths: Insight[];
  challenges: Insight[];
  patterns: Insight[];
  proposedAction: string;
  generatedAt: string;
}

export type ReportSection = "takeaways" | "strengths" | "challenges" | "patterns";

export interface Commitment {
  id: string;
  reviewId: string;
  /** Week the commitment is made in (the reviewed week); applies to the following week */
  weekStart: string;
  text: string;
  measure: string;
  createdAt: string;
}

export interface SaveReviewInput {
  id?: string | undefined;
  weekStart: string;
  answers: Answers;
  freeWriting: string;
  followUps: FollowUp[];
  previousAction?: PreviousActionCheck | undefined;
}

export const emptyAnswers = (): Answers => ({
  wentWell: "",
  didntGoWell: "",
  handledBetter: "",
  learned: "",
  doDifferently: "",
});
