import type { Insight, Report, Review, SaveReviewInput } from "../types";

const STOP = new Set(
  "about after again also always because been before being could didn doing during every from have having into just like made make more most much never only other really should some than that their them then there these they thing things this those through time very want week were what when where which while with would your myself".split(
    " ",
  ),
);

let counter = 0;
const uid = (p: string) => `${p}_${Date.now().toString(36)}_${(counter++).toString(36)}`;

export function sentences(text: string): string[] {
  return text
    .split(/(?<=[.!?])\s+|\n+/)
    .map((s) => s.trim())
    .filter((s) => s.length > 2);
}

export function keywords(text: string): Set<string> {
  return new Set(
    (text.toLowerCase().match(/[a-z']+/g) ?? [])
      .map((w) => w.replace(/'s$/, ""))
      .filter((w) => w.length >= 5 && !STOP.has(w)),
  );
}

const reviewText = (r: Pick<Review, "answers" | "freeWriting" | "followUps">) =>
  [...Object.values(r.answers), r.freeWriting, ...r.followUps.map((f) => f.answer)].join(" ");

const insight = (text: string, kind: Insight["kind"], evidence: string): Insight => ({
  id: uid("ins"),
  text,
  kind,
  evidence,
  status: "pending",
});

export function suggestFollowUps(r: SaveReviewInput): string[] {
  const q: string[] = [];
  const a = r.answers;
  const bad = sentences(a.didntGoWell)[0];
  if (bad) q.push(`Looking at "${bad}" — which part of that was within your control?`);
  if (a.wentWell.trim().length < 40)
    q.push("What's one small thing that went well that you might be overlooking?");
  if (!a.learned.trim())
    q.push("If a friend had lived your week, what would you tell them they learned?");
  const plan = a.doDifferently.trim();
  if (
    plan &&
    !/\d|daily|every|each|monday|tuesday|wednesday|thursday|friday|morning|evening/i.test(plan)
  )
    q.push("How will you know, concretely, that you did this next week?");
  if (!plan) q.push("If you could change just one thing next week, what would it be?");
  return q.slice(0, 3);
}

export function generateReport(review: Review, history: Review[]): Report {
  const a = review.answers;
  const takeaways: Insight[] = [];
  const strengths: Insight[] = [];
  const challenges: Insight[] = [];
  const patterns: Insight[] = [];

  const learned = sentences(a.learned);
  if (learned[0])
    takeaways.push(
      insight(`You noticed something about yourself: ${learned[0]}`, "observation", learned[0]),
    );
  const good = sentences(a.wentWell);
  const bad = sentences(a.didntGoWell);
  if (good.length && bad.length)
    takeaways.push(
      insight(
        `The week was mixed: progress alongside friction. Both sides are worth keeping in view.`,
        "observation",
        `${good[0]} / ${bad[0]}`,
      ),
    );

  for (const s of good.slice(0, 3))
    strengths.push(insight(`Something worked: ${s}`, "observation", s));

  for (const s of bad.slice(0, 2))
    challenges.push(insight(`A difficulty you named: ${s}`, "observation", s));
  const better = sentences(a.handledBetter)[0];
  if (better)
    challenges.push(
      insight(
        `Possible blind spot: this may be a recurring response under pressure, not a one-off. Worth checking whether it shows up elsewhere.`,
        "hypothesis",
        better,
      ),
    );

  const pa = review.previousAction;
  if (pa && (pa.attempted === "no" || pa.attempted === "partly")) {
    challenges.push(
      insight(
        `Last week's commitment was ${pa.attempted === "no" ? "not attempted" : "only partly done"}. It may have been too big or poorly timed — consider making the next one smaller.`,
        "hypothesis",
        pa.whatHappened || `Attempted: ${pa.attempted}`,
      ),
    );
  } else if (pa?.attempted === "yes") {
    strengths.push(
      insight(
        "You followed through on last week's commitment.",
        "observation",
        pa.whatHappened || "Attempted: yes",
      ),
    );
  }

  // Patterns: keywords in this review that also appear in past completed reviews
  const past = history.filter((h) => h.id !== review.id && h.status === "completed");
  if (past.length) {
    const mine = keywords(reviewText(review));
    const counts: { word: string; weeks: string[] }[] = [];
    for (const w of mine) {
      const weeks = past.filter((p) => keywords(reviewText(p)).has(w)).map((p) => p.weekStart);
      if (weeks.length) counts.push({ word: w, weeks });
    }
    counts.sort((x, y) => y.weeks.length - x.weeks.length || x.word.localeCompare(y.word));
    for (const c of counts.slice(0, 3)) {
      patterns.push(
        insight(
          `"${c.word}" has come up in ${c.weeks.length + 1} of your reviews. This might be a recurring theme — or a coincidence.`,
          "hypothesis",
          `Also mentioned in weeks of ${c.weeks.sort().join(", ")}`,
        ),
      );
    }
  }

  const plan = sentences(a.doDifferently)[0];
  const proposedAction = plan
    ? plan
    : bad[0]
      ? `Pick one specific moment this week to respond differently to: "${bad[0]}"`
      : "";

  return {
    id: uid("rep"),
    reviewId: review.id,
    takeaways,
    strengths,
    challenges,
    patterns,
    proposedAction,
    generatedAt: new Date().toISOString(),
  };
}
