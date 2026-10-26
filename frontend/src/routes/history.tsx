import { createFileRoute, Link } from "@tanstack/react-router";
import { useQueryClient, useSuspenseQuery } from "@tanstack/react-query";
import { useState } from "react";
import { toast } from "sonner";
import { Button } from "@/components/ui/button";
import { formatWeek, services, type Review } from "@/services";
import { qk, reviewsQuery } from "@/services/queries";
import { requireAuthenticated } from "@/lib/require-auth";
import { PageLoading } from "@/components/page-loading";

export const Route = createFileRoute("/history")({
  ssr: false,
  beforeLoad: requireAuthenticated,
  pendingComponent: PageLoading,
  head: () => ({
    meta: [
      { title: "Weekly — Past reviews" },
      { name: "description", content: "Browse your past weekly reflections and feedback." },
      { property: "og:title", content: "Weekly — Past reviews" },
      { property: "og:description", content: "Every weekly reflection and report in one place." },
    ],
  }),
  loader: ({ context: { queryClient } }) => queryClient.ensureQueryData(reviewsQuery()),
  component: History,
});

function History() {
  const { data: reviews } = useSuspenseQuery(reviewsQuery());
  const qc = useQueryClient();
  const [deletingAll, setDeletingAll] = useState(false);

  return (
    <div className="space-y-8 pt-4">
      <h1 className="text-4xl font-semibold">Past reviews</h1>
      {reviews.length === 0 ? (
        <p className="text-muted-foreground">No reviews yet.</p>
      ) : (
        <ul className="space-y-3">
          {reviews.map((r) => (
            <li key={r.id} className="flex items-center gap-3">
              <Link
                to={r.status === "completed" ? "/report/$reviewId" : "/review"}
                params={{ reviewId: r.id }}
                search={r.status === "completed" ? {} : { week: r.weekStart }}
                className="min-w-0 flex-1 rounded-xl border bg-card p-5 hover:shadow-soft"
              >
                <div className="flex justify-between">
                  <span className="font-serif text-lg">{formatWeek(r.weekStart)}</span>
                  <span className="text-sm text-muted-foreground">
                    {r.status === "completed" ? "Completed" : "Draft"}
                  </span>
                </div>
                {r.answers.learned && (
                  <p className="mt-2 line-clamp-2 text-sm text-muted-foreground">
                    Learned: {r.answers.learned}
                  </p>
                )}
              </Link>
              {r.status === "draft" && <DraftDeleteButton review={r} />}
            </li>
          ))}
        </ul>
      )}
      <section className="rounded-xl border border-destructive/30 p-5">
        <h2 className="text-lg">Your data</h2>
        <p className="mt-1 text-sm text-muted-foreground">
          Everything is private. You can erase all reflections, reports and commitments.
        </p>
        <Button
          variant="outline"
          className="mt-3 text-destructive"
          disabled={deletingAll}
          onClick={async () => {
            if (!confirm("Permanently delete all your data?")) return;
            setDeletingAll(true);
            try {
              await services.deleteAllData();
              qc.setQueryData(qk.reviews, []);
              qc.removeQueries({ predicate: (query) => query.queryKey[0] !== qk.reviews[0] });
              toast.success("All data deleted");
            } catch {
              toast.error("Your data couldn't be deleted. Please try again.");
            } finally {
              setDeletingAll(false);
            }
          }}
        >
          {deletingAll ? "Deleting…" : "Delete all my data"}
        </Button>
      </section>
    </div>
  );
}

export function DraftDeleteButton({ review }: { review: Review }) {
  const qc = useQueryClient();
  const [deleting, setDeleting] = useState(false);
  return (
    <Button
      type="button"
      variant="ghost"
      className="shrink-0 text-destructive"
      disabled={deleting}
      onClick={async () => {
        if (!confirm(`Delete the saved draft for ${formatWeek(review.weekStart)}?`)) return;
        setDeleting(true);
        try {
          await services.deleteReview(review.id);
          qc.setQueryData<Review[]>(qk.reviews, (current) =>
            current?.filter((item) => item.id !== review.id),
          );
          await qc.invalidateQueries();
          toast.success("Draft deleted");
        } catch {
          toast.error("This draft couldn't be deleted. Please try again.");
        } finally {
          setDeleting(false);
        }
      }}
    >
      {deleting ? "Deleting…" : `Delete draft ${formatWeek(review.weekStart)}`}
    </Button>
  );
}
