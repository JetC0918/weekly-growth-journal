import { createFileRoute, useNavigate } from "@tanstack/react-router";
import { useQueryClient, useSuspenseQuery } from "@tanstack/react-query";
import { useState } from "react";
import { toast } from "sonner";
import { z } from "zod";
import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";
import { Label } from "@/components/ui/label";
import {
  emptyAnswers,
  formatWeek,
  PROMPTS,
  services,
  weekStartOf,
  type PreviousActionCheck,
  type Commitment,
  type Review,
  type SaveReviewInput,
} from "@/services";
import { commitmentBeforeQuery, weekReviewQuery } from "@/services/queries";
import { requireAuthenticated } from "@/lib/require-auth";
import { PageLoading } from "@/components/page-loading";

export const Route = createFileRoute("/review")({
  ssr: false,
  beforeLoad: requireAuthenticated,
  pendingComponent: PageLoading,
  validateSearch: z.object({
    week: z
      .string()
      .regex(/^\d{4}-\d{2}-\d{2}$/)
      .optional(),
  }),
  head: () => ({
    meta: [
      { title: "Weekly — Reflect on your week" },
      { name: "description", content: "Answer five short prompts and reflect on your week." },
      { property: "og:title", content: "Weekly — Reflect on your week" },
      {
        property: "og:description",
        content: "Five prompts, free writing, and optional follow-up questions.",
      },
    ],
  }),
  loaderDeps: ({ search }) => ({ week: search.week ?? weekStartOf() }),
  loader: ({ context: { queryClient }, deps }) =>
    Promise.all([
      queryClient.ensureQueryData(weekReviewQuery(deps.week)),
      queryClient.ensureQueryData(commitmentBeforeQuery(deps.week)),
    ]),
  component: ReviewPage,
});

function ReviewPage() {
  const { week = weekStartOf() } = Route.useSearch();
  const { data: existing } = useSuspenseQuery(weekReviewQuery(week));
  const { data: prev } = useSuspenseQuery(commitmentBeforeQuery(week));
  const navigate = useNavigate();
  return (
    <ReviewEditor
      week={week}
      existing={existing}
      previousCommitment={prev}
      onCompleted={(id) => navigate({ to: "/report/$reviewId", params: { reviewId: id } })}
    />
  );
}

export function ReviewEditor({
  week,
  existing,
  previousCommitment: prev,
  onCompleted,
}: {
  week: string;
  existing: Review | null;
  previousCommitment: Commitment | null;
  onCompleted: (id: string) => void;
}) {
  const qc = useQueryClient();

  const [answers, setAnswers] = useState(existing?.answers ?? emptyAnswers());
  const [freeWriting, setFree] = useState(existing?.freeWriting ?? "");
  const [followUps, setFollowUps] = useState(existing?.followUps ?? []);
  const [pa, setPa] = useState<PreviousActionCheck | undefined>(
    existing?.previousAction ??
      (prev ? { commitmentId: prev.id, attempted: "", whatHappened: "", learned: "" } : undefined),
  );
  const [busy, setBusy] = useState<"" | "save" | "ask" | "finish">("");
  const isCompleted = existing?.status === "completed";

  const input = (): SaveReviewInput => ({
    id: existing?.id,
    weekStart: week,
    answers,
    freeWriting,
    followUps,
    previousAction: pa,
  });
  const hasContent = Object.values(answers).some((a) => a.trim()) || freeWriting.trim();

  const save = async () => {
    const r = await services.saveReview(input());
    qc.invalidateQueries();
    return r;
  };

  return (
    <div className="space-y-8 pt-4">
      <div>
        <p className="text-sm uppercase tracking-widest text-muted-foreground">
          {formatWeek(week)}
        </p>
        <h1 className="mt-2 text-4xl font-semibold">Weekly reflection</h1>
        <p className="mt-2 text-muted-foreground">
          Short answers are fine. Skip anything that doesn't apply.
        </p>
      </div>

      {prev && pa && (
        <section className="space-y-4 rounded-xl border border-accent/40 bg-card p-6 shadow-soft">
          <p className="text-xs font-semibold uppercase tracking-widest text-accent">
            Last week you committed to
          </p>
          <p className="font-serif text-xl">{prev.text}</p>
          <div className="flex flex-wrap gap-2" role="radiogroup" aria-label="Did you attempt it?">
            {(["yes", "partly", "no"] as const).map((v) => (
              <Button
                key={v}
                type="button"
                size="sm"
                variant={pa.attempted === v ? "default" : "outline"}
                aria-pressed={pa.attempted === v}
                onClick={() => setPa({ ...pa, attempted: v })}
              >
                {v === "yes" ? "I did it" : v === "partly" ? "Partly" : "Not really"}
              </Button>
            ))}
          </div>
          <Field
            label="What happened?"
            value={pa.whatHappened}
            onChange={(v) => setPa({ ...pa, whatHappened: v })}
            rows={2}
          />
          <Field
            label="What did you learn from it?"
            value={pa.learned}
            onChange={(v) => setPa({ ...pa, learned: v })}
            rows={2}
          />
        </section>
      )}

      <section className="space-y-6">
        {PROMPTS.map((p, i) => (
          <Field
            key={p.id}
            label={`${i + 1}. ${p.label}`}
            value={answers[p.id]}
            onChange={(v) => setAnswers({ ...answers, [p.id]: v })}
          />
        ))}
        <Field
          label="Anything else on your mind? (free writing)"
          value={freeWriting}
          onChange={setFree}
          rows={5}
        />
      </section>

      <section className="space-y-4 rounded-xl bg-secondary p-6">
        <div className="flex flex-wrap items-center justify-between gap-3">
          <div>
            <h2 className="text-xl">Go deeper</h2>
            <p className="text-sm text-muted-foreground">
              Optional AI follow-up questions based on what you wrote.
            </p>
          </div>
          <Button
            variant="outline"
            disabled={busy !== "" || !hasContent}
            onClick={async () => {
              setBusy("ask");
              try {
                const qs = await services.suggestFollowUps(input());
                const known = new Set(followUps.map((f) => f.question));
                setFollowUps([
                  ...followUps,
                  ...qs.filter((q) => !known.has(q)).map((question) => ({ question, answer: "" })),
                ]);
              } catch {
                toast.error("We couldn't get follow-up questions. Your reflection is still here.");
              } finally {
                setBusy("");
              }
            }}
          >
            {busy === "ask" ? "Thinking…" : "Ask me questions"}
          </Button>
        </div>
        {followUps.map((f, i) => (
          <Field
            key={f.question}
            label={f.question}
            value={f.answer}
            rows={2}
            onChange={(v) =>
              setFollowUps(followUps.map((x, j) => (j === i ? { ...x, answer: v } : x)))
            }
          />
        ))}
      </section>

      <div className="flex flex-wrap gap-3">
        <Button
          size="lg"
          disabled={busy !== "" || !hasContent}
          onClick={async () => {
            setBusy("finish");
            try {
              const r = await save();
              await services.completeReview(r.id);
              await qc.invalidateQueries();
              onCompleted(r.id);
            } catch {
              toast.error(
                "We couldn't complete your review. Your answers are still here; please try again.",
              );
            } finally {
              setBusy("");
            }
          }}
        >
          {busy === "finish"
            ? isCompleted
              ? "Refreshing feedback…"
              : "Preparing feedback…"
            : isCompleted
              ? "Refresh feedback"
              : "Finish & get feedback"}
        </Button>
        <Button
          size="lg"
          variant="outline"
          disabled={busy !== ""}
          onClick={async () => {
            setBusy("save");
            try {
              await save();
              toast.success(
                isCompleted ? "Changes saved; feedback was not refreshed" : "Draft saved",
              );
            } catch {
              toast.error(
                "Your draft couldn't be saved. Your answers are still here; please try again.",
              );
            } finally {
              setBusy("");
            }
          }}
        >
          {isCompleted ? "Save changes without refreshing feedback" : "Save draft"}
        </Button>
      </div>
    </div>
  );
}

function Field({
  label,
  value,
  onChange,
  rows = 3,
}: {
  label: string;
  value: string;
  onChange: (v: string) => void;
  rows?: number;
}) {
  const id = label.replace(/\W+/g, "-").toLowerCase();
  return (
    <div className="space-y-2">
      <Label htmlFor={id} className="text-base font-medium">
        {label}
      </Label>
      <Textarea
        id={id}
        rows={rows}
        value={value}
        onChange={(e) => onChange(e.target.value)}
        className="bg-card"
      />
    </div>
  );
}
