import { createFileRoute, Link } from "@tanstack/react-router";
import { useQueryClient, useSuspenseQuery } from "@tanstack/react-query";
import { toast } from "sonner";
import { Button } from "@/components/ui/button";
import { formatWeek, services } from "@/services";
import { reviewsQuery } from "@/services/queries";

export const Route = createFileRoute("/history")({
  ssr: false,
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
  return (
    <div className="space-y-8 pt-4">
      <h1 className="text-4xl font-semibold">Past reviews</h1>
      {reviews.length === 0 ? (
        <p className="text-muted-foreground">No reviews yet.</p>
      ) : (
        <ul className="space-y-3">
          {reviews.map((r) => (
            <li key={r.id}>
              <Link
                to={r.status === "completed" ? "/report/$reviewId" : "/review"}
                params={{ reviewId: r.id }}
                search={r.status === "completed" ? undefined : { week: r.weekStart }}
                className="block rounded-xl border bg-card p-5 hover:shadow-soft"
              >
                <div className="flex justify-between">
                  <span className="font-serif text-lg">{formatWeek(r.weekStart)}</span>
                  <span className="text-sm text-muted-foreground">{r.status === "completed" ? "Completed" : "Draft"}</span>
                </div>
                {r.answers.learned && (
                  <p className="mt-2 line-clamp-2 text-sm text-muted-foreground">Learned: {r.answers.learned}</p>
                )}
              </Link>
            </li>
          ))}
        </ul>
      )}
      <section className="rounded-xl border border-destructive/30 p-5">
        <h2 className="text-lg">Your data</h2>
        <p className="mt-1 text-sm text-muted-foreground">Everything is private. You can erase all reflections, reports and commitments.</p>
        <Button
          variant="outline"
          className="mt-3 text-destructive"
          onClick={async () => {
            if (!confirm("Permanently delete all your data?")) return;
            await services.deleteAllData();
            qc.invalidateQueries();
            toast.success("All data deleted");
          }}
        >
          Delete all my data
        </Button>
      </section>
    </div>
  );
}
