type Props = {
  defaultValue?: string;
  autoFocus?: boolean;
  /** Extra filters to keep when searching again from a results page. */
  hidden?: [string, string][];
};

/** The reader's line, lettered in a speech balloon. A plain GET form: works without JavaScript. */
export default function SearchBalloon({ defaultValue = "", autoFocus = false, hidden = [] }: Props) {
  return (
    <form action="/search" method="get" role="search" className="balloon-row">
      <label className="balloon">
        <span className="visually-hidden">Describe the story you want to read</span>
        <input
          type="search"
          name="q"
          defaultValue={defaultValue}
          placeholder="a detective who can see ghosts…"
          maxLength={200}
          required
          autoFocus={autoFocus}
          autoComplete="off"
          enterKeyHint="search"
        />
      </label>
      {hidden.map(([name, value], i) => (
        <input key={`${name}-${i}`} type="hidden" name={name} value={value} />
      ))}
      <button type="submit" className="btn">
        Find comics
      </button>
    </form>
  );
}
