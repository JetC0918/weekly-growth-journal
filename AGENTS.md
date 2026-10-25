<!-- LOVABLE:BEGIN -->
> [!IMPORTANT]
> This project is connected to [Lovable](https://lovable.dev). Avoid rewriting
> published git history — force pushing, or rebasing/amending/squashing commits
> that are already pushed — as it rewrites history on Lovable's side and the
> user will likely lose their project history.
>
> Commits you push to the connected branch sync back to Lovable and show up in
> the editor, so keep the branch in a working state.
<!-- LOVABLE:END -->

## Architecture rules
- All backend calls go through the `GrowthService` interface in `src/services/api.ts`; UI imports only `services` from `src/services` — so the mock can be swapped for a real backend in one place.
- `src/services/mock/` holds the mock implementation (localStorage-backed) and heuristic "AI"; keep it pure and testable with an in-memory store.
- Data routes use `ssr: false` because the mock reads browser storage.
