type Props = {
  value: string;
  onChange: (value: string) => void;
};

export function PromptBox({ value, onChange }: Props) {
  return (
    <div className="panel">
      <label htmlFor="promptBox">Prompt</label>
      <textarea
        id="promptBox"
        rows={4}
        value={value}
        onChange={(event) => onChange(event.target.value)}
        placeholder="Analyze this table and show problems."
      />
    </div>
  );
}

