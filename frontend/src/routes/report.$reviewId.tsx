import { createFileRoute, Link, notFound, useNavigate } from "@tanstack/react-router";
import { useQueryClient, useSuspenseQuery } from "@tanstack/react-query";
import { useState } from "react";
import { toast } from "sonner";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import { formatWeek, nextWeekStart, services, type Insight, type ReportSection } from "@/services";
import { commitmentQuery, qk, reportQuery, reviewQuery } from "@/services/queries";
import { requireAuthenticated } from "@/lib/require-auth";
import { PageLoading } from "@/components/page-loading";

export const Route = createFileRoute("/report/$reviewId")({
  ssr: false,
  beforeLoad: requireAuthenticated,
  pendingComponent: PageLoading,
  head: () => ({
    meta: [
      { title: "Weekly — Your feedback report" },
      {
        name: "description",
        content: "Takeaways, strengths, challenges and one action for next week.",
      },
      { property: "og:title", content: "Weekly — Your feedback report" },
      {
        property: "og:description",
        content: "Evidence-grounded feedback on your weekly reflection.",
      },
    ],
  }),
  loader: async ({ context: { queryClient }, params }) => {
    const [review, report] = await Promise.all([
      queryClient.ensureQueryData(reviewQuery(params.reviewId)),
      queryClient.ensureQueryData(reportQuery(params.reviewId)),
      queryClient.ensureQueryData(commitmentQuery(params.reviewId)),
    ]);
    if (!review || !report) throw notFound();
  },
  component: ReportPage,
});

const SECTIONS: { key: ReportSection; title: string }[] = [
  { key: "takeaways", title: "Key takeaways" },
  { key: "strengths", title: "Strengths" },
  { key: "challenges", title: "Challenges & possible blind spots" },
  { key: "patterns", title: "Recurring patterns" },
];

function ReportPage() {
  const { reviewId } = Route.useParams();
  const { data: review } = useSuspenseQuery(reviewQuery(reviewId));
  const { data: report } = useSuspenseQuery(reportQuery(reviewId));
  const { data: commitment } = useSuspenseQuery(commitmentQuery(reviewId));
  const qc = useQueryClient();
  const navigate = useNavigate();
  const [text, setText] = useState(commitment?.text ?? report?.proposedAction ?? "");
  const [measure, setMeasure] = useState(commitment?.measure ?? "");
  const [savingCommitment, setSavingCommitment] = useState(false);
  const [deletingReview, setDeletingReview] = useState(false);
  if (!review || !report) return null;

  const update = async (section: ReportSection, id: string, patch: Partial<Insight>) => {
    try {
      const next = await services.updateInsight(reviewId, section, id, patch);
      qc.setQueryData(qk.report(reviewId), next);
      return true;
    } catch {
      toast.error("That change couldn't be saved. Please try again.");
      return false;
    }
  };

  return (
    <div className="space-y-10 pt-4">
      <div>
        <p className="text-sm uppercase tracking-widest text-muted-foreground">
          {formatWeek(review.weekStart)}
        </p>
        <h1 className="mt-2 text-4xl font-semibold">Your feedback</h1>
        <p className="mt-2 text-sm text-muted-foreground">
          Generated from your own words.{" "}
          <span className="font-medium text-observation-foreground">Observations</span> restate what
          you wrote; <span className="font-medium text-hypothesis-foreground">hypotheses</span> are
          interpretations that may be wrong — accept, reject or correct them.
        </p>
      </div>

      {SECTIONS.map(({ key, title }) => (
        <section key={key} className="space-y-3">
          <h2 className="text-2xl">{title}</h2>
          {report[key].length === 0 ? (
            <p className="text-sm text-muted-foreground">
              {key === "patterns"
                ? "Not enough history yet. Patterns appear after a few weeks."
                : "Nothing here — there wasn't enough detail to say."}
            </p>
          ) : (
            report[key].map((i) => (
              <InsightCard key={i.id} insight={i} onChange={(p) => update(key, i.id, p)} />
            ))
          )}
        </section>
      ))}

      <section className="space-y-4 rounded-xl border-2 border-primary/30 bg-card p-6 shadow-soft">
        <p className="text-xs font-semibold uppercase tracking-widest text-accent">
          One commitment for next week
        </p>
        <div className="space-y-2">
          <Label htmlFor="commit">What will you do?</Label>
          <Textarea
            id="commit"
            rows={2}
            value={text}
            onChange={(e) => setText(e.target.value)}
            className="font-serif text-lg"
          />
        </div>
        <div className="space-y-2">
          <Label htmlFor="measure">How will you know you did it? (optional)</Label>
          <Input
            id="measure"
            value={measure}
            onChange={(e) => setMeasure(e.target.value)}
            placeholder="e.g. 3 of 5 workdays"
          />
        </div>
        <Button
          disabled={!text.trim() || savingCommitment}
          onClick={async () => {
            setSavingCommitment(true);
            try {
              await services.setCommitment(reviewId, { text, measure });
              await qc.invalidateQueries();
              toast.success("Commitment saved");
            } catch {
              toast.error(
                "Your commitment couldn't be saved. Your text is still here; please try again.",
              );
            } finally {
              setSavingCommitment(false);
            }
          }}
        >
          {savingCommitment ? "Saving…" : commitment ? "Update commitment" : "Commit to this"}
        </Button>
      </section>

      <div className="flex flex-wrap gap-3 border-t pt-6">
        <Button asChild variant="outline">
          <Link to="/review" search={{ week: review.weekStart }}>
            Edit reflection
          </Link>
        </Button>
        <Button asChild variant="outline">
          <Link to="/review" search={{ week: nextWeekStart(review.weekStart) }}>
            Open next week&apos;s reflection
          </Link>
        </Button>
        <Button
          variant="ghost"
          className="text-destructive"
          disabled={deletingReview}
          onClick={async () => {
            if (!confirm("Delete this review, its feedback and commitment?")) return;
            setDeletingReview(true);
            try {
              await services.deleteReview(reviewId);
              await qc.invalidateQueries();
              navigate({ to: "/history" });
            } catch {
              toast.error("This review couldn't be deleted. Please try again.");
              setDeletingReview(false);
            }
          }}
        >
          {deletingReview ? "Deleting…" : "Delete this review"}
        </Button>
      </div>
    </div>
  );
}

function InsightCard({
  insight,
  onChange,
}: {
  insight: Insight;
  onChange: (p: Partial<Insight>) => Promise<boolean>;
}) {
  const [editing, setEditing] = useState(false);
  const [draft, setDraft] = useState(insight.correction ?? "");
  const [saving, setSaving] = useState(false);
  const rejected = insight.status === "rejected";
  const change = async (patch: Partial<Insight>) => {
    setSaving(true);
    try {
      return await onChange(patch);
    } finally {
      setSaving(false);
    }
  };
  return (
    <article className={`rounded-xl border bg-card p-5 ${rejected ? "opacity-50" : ""}`}>
      <span
        className={`inline-block rounded-full px-2 py-0.5 text-xs font-medium ${
          insight.kind === "hypothesis"
            ? "bg-hypothesis text-hypothesis-foreground"
            : "bg-observation text-observation-foreground"
        }`}
      >
        {insight.kind === "hypothesis" ? "Hypothesis" : "Observation"}
      </span>
      <p className={`mt-2 ${rejected ? "line-through" : ""}`}>{insight.text}</p>
      <p className="mt-2 border-l-2 border-border pl-3 text-sm italic text-muted-foreground">
        Based on: “{insight.evidence}”
      </p>
      {insight.correction && !editing && (
        <p className="mt-2 text-sm">
          <span className="font-medium">Your correction:</span> {insight.correction}
        </p>
      )}
      {editing && (
        <div className="mt-3 flex gap-2">
          <Input
            value={draft}
            onChange={(e) => setDraft(e.target.value)}
            placeholder="What's actually true?"
          />
          <Button
            size="sm"
            disabled={saving}
            onClick={async () => {
              if (await change({ correction: draft })) setEditing(false);
            }}
          >
            {saving ? "Saving…" : "Save"}
          </Button>
        </div>
      )}
      <div className="mt-3 flex gap-1 text-sm">
        <Button
          size="sm"
          disabled={saving}
          variant={insight.status === "accepted" ? "default" : "ghost"}
          onClick={() =>
            void change({ status: insight.status === "accepted" ? "pending" : "accepted" })
          }
        >
          Accurate
        </Button>
        <Button
          size="sm"
          disabled={saving}
          variant={rejected ? "default" : "ghost"}
          onClick={() => void change({ status: rejected ? "pending" : "rejected" })}
        >
          Not right
        </Button>
        <Button size="sm" disabled={saving} variant="ghost" onClick={() => setEditing(!editing)}>
          Correct it
        </Button>
      </div>
    </article>
  );
}
