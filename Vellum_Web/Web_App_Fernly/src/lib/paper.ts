/**
 * The minimum a paper must carry to be added to a notebook.
 *
 * Three screens produce papers — academic search, screening and the citation
 * graph — and each has its own richer shape. They all converge on the
 * "Add to notebook" modal, which only ever reads the fields below. Declaring
 * that here means the modal no longer accepts `any`, which used to hide a real
 * bug: screening results carry their title under `journal`, not `venue`, so
 * they were saved to the notebook with no journal at all.
 */
export interface AddablePaper {
  title: string;
  authors: string[];
  year: number;
  doi?: string;
  /** Journal or venue, under whichever name the producing screen uses. */
  venue?: string;
  journal?: string;
}
