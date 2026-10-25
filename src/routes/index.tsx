import { createFileRoute, Link } from "@tanstack/react-router";
import { useSuspenseQuery } from "@tanstack/react-query";
import { Button } from "@/components/ui/button";
import { formatWeek, weekStartOf } from "@/services";
import { commitmentBeforeQuery, reviewsQuery, weekReviewQuery } from "@/services/queries";

export const Route = createFileRoute("/")({
  ssr: false,
  head: () => ({
    meta: [
      { title: "Weekly — Your growth this week" },
      { name: "description", content: "See this week's review status and your current improvement commitment." },
      { property: "og:title", content: "Weekly — Your growth this week" },
      { property: "og:description", content: "A private weekly reflection and feedback companion." },
    ],
  }),
  loader: ({ context: { queryClient } }) => {
    const w = weekStartOf();
    return Promise.all([
      queryClient.ensureQueryData(weekReviewQuery(w)),
      queryClient.ensureQueryData(commitmentBeforeQuery(w)),
      queryClient.ensureQueryData(reviewsQuery()),
    ]);
  },
  component: Home,
});

function Home() {
  const w = weekStartOf();
  const { data: current } = useSuspenseQuery(weekReviewQuery(w));
  const { data: commitment } = useSuspenseQuery(commitmentBeforeQuery(w));
  const { data: reviews } = useSuspenseQuery(reviewsQuery());
  const past = reviews.filter((r) => r.weekStart !== w).slice(0, 4);
  const status = !current ? "Not started" : current.status === "draft" ? "In progress" : "Completed";

  return (
    <div className="space-y-10">
      <section className="pt-6">
        <p className="text-sm uppercase tracking-widest text-muted-foreground">{formatWeek(w)}</p>
        <h1 className="mt-3 text-4xl font-semibold leading-tight sm:text-5xl">
          A little better, <em className="text-accent">every week.</em>
        </h1>
        <div className="mt-8 flex flex-wrap items-center gap-4">
          {current?.status === "completed" ? (
            <Button asChild size="lg">
              <Link to="/report/$reviewId" params={{ reviewId: current.id }}>View this week's feedback</Link>
            </Button>
          ) : (
            <Button asChild size="lg">
              <Link to="/review">{current ? "Continue your review" : "Start this week's review"}</Link>
            </Button>
          )}
          <span className="rounded-full bg-secondary px-3 py-1 text-sm text-secondary-foreground">{status}</span>
        </div>
      </section>

      <section className="rounded-xl border bg-card p-6 shadow-soft">
        <p className="text-xs font-semibold uppercase tracking-widest text-accent">Your commitment this week</p>
        {commitment ? (
          <>
            <p className="mt-3 font-serif text-2xl">{commitment.text}</p>
            {commitment.measure && (
              <p className="mt-2 text-sm text-muted-foreground">How you'll know: {commitment.measure}</p>
            )}
          </>
        ) : (
          <p className="mt-3 text-muted-foreground">
            No commitment yet. Finish a review to choose one thing to work on.
          </p>
        )}
      </section>

      <section>
        <div className="flex items-baseline justify-between">
          <h2 className="text-2xl">Previous weeks</h2>
          <Link to="/history" className="text-sm text-primary underline-offset-4 hover:underline">
            See all
          </Link>
        </div>
        {past.length === 0 ? (
          <p className="mt-4 text-muted-foreground">Your past reviews will appear here.</p>
        ) : (
          <ul className="mt-4 divide-y rounded-xl border bg-card">
            {past.map((r) => (
              <li key={r.id}>
                <Link
                  to={r.status === "completed" ? "/report/$reviewId" : "/review"}
                  params={{ reviewId: r.id }}
                  search={r.status === "completed" ? undefined : { week: r.weekStart }}
                  className="flex justify-between px-5 py-4 hover:bg-muted"
                >
                  <span>{formatWeek(r.weekStart)}</span>
                  <span className="text-sm text-muted-foreground">{r.status === "completed" ? "Completed" : "Draft"}</span>
                </Link>
              </li>
            ))}
          </ul>
        )}
      </section>
    </div>
  );
}
