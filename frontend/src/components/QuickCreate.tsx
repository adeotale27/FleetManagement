import { useNavigate } from "react-router-dom";
import { Button } from "./ui/primitives";

const ITEMS = [
  ["New Trip", "/trips/new"],
  ["New LR", "/lrs/new"],
  ["Collection", "/collections/new"],
  ["Payment", "/finance"],
  ["Expense", "/expenses/new"],
  ["Fuel Entry", "/fuel/new"],
  ["Driver", "/drivers"],
  ["Vehicle", "/vehicles"],
  ["Party", "/parties"],
  ["Employee Advance", "/people"],
];

export function QuickCreate({ onDone }: { onDone: () => void }) {
  const navigate = useNavigate();
  return (
    <div className="grid">
      {ITEMS.map(([label, to]) => (
        <Button
          key={label}
          variant="secondary"
          onClick={() => {
            navigate(to);
            onDone();
          }}
        >
          {label}
        </Button>
      ))}
    </div>
  );
}
