import { Recommendation } from "../../types";
import { ShoppingCart, ExternalLink } from "lucide-react";

// Compound registry — maps compound_id to purchase info
const COMPOUND_LINKS: Record<string, { name: string; link: string; price: string }> = {
  nac: {
    name: "NAC 600mg",
    link: "https://www.amazon.com/s?k=NAC+600mg+N-Acetyl+Cysteine",
    price: "~$18/mo",
  },
  milk_thistle: {
    name: "Milk Thistle Extract",
    link: "https://www.amazon.com/s?k=Milk+Thistle+Extract+Silymarin",
    price: "~$12/mo",
  },
  rhodiola: {
    name: "Rhodiola Rosea 500mg",
    link: "https://www.amazon.com/s?k=Rhodiola+Rosea+500mg",
    price: "~$20/mo",
  },
  nmn: {
    name: "NMN 500mg",
    link: "https://www.amazon.com/s?k=NMN+500mg+supplement",
    price: "~$45/mo",
  },
  berberine: {
    name: "Berberine 500mg",
    link: "https://www.amazon.com/s?k=Berberine+500mg",
    price: "~$22/mo",
  },
};

interface Props {
  recommendations: Recommendation[];
}

export default function CompoundCart({ recommendations }: Props) {
  // Find "add" recommendations as cart items
  const addRecs = recommendations.filter((r) => r.action_type === "add");

  // Also suggest reduced-load alternatives
  const swapRecs = recommendations.filter((r) => r.action_type === "swap");

  const cartItems = addRecs
    .map((rec) => {
      // Extract compound id from rec id (e.g. "add_nac" → "nac")
      const id = rec.id.replace("add_", "");
      return COMPOUND_LINKS[id]
        ? { ...COMPOUND_LINKS[id], rec }
        : null;
    })
    .filter(Boolean) as Array<{ name: string; link: string; price: string; rec: Recommendation }>;

  if (cartItems.length === 0 && swapRecs.length === 0) {
    return null;
  }

  return (
    <div className="bg-white rounded-2xl shadow-sm border border-blue-gray-100 p-6 mt-8">
      <div className="flex items-center gap-3 mb-5">
        <div className="w-10 h-10 bg-blue-gray-900 rounded-xl flex items-center justify-center">
          <ShoppingCart className="w-5 h-5 text-white" />
        </div>
        <div>
          <h3 className="font-serif font-bold text-xl text-blue-gray-900">Supplement Protocol Cart</h3>
          <p className="text-sm text-blue-gray-500">Recommended compounds from your optimization plan</p>
        </div>
      </div>

      <div className="space-y-3">
        {cartItems.map(({ name, link, price, rec }) => (
          <div key={rec.id} className="flex items-center justify-between p-4 rounded-xl border border-brand-green/20 bg-brand-green/5 hover:bg-brand-green/10 transition-colors">
            <div>
              <p className="font-bold text-blue-gray-900">{name}</p>
              <p className="text-xs text-blue-gray-500 mt-0.5">{rec.title} • {price}</p>
            </div>
            <a
              href={link}
              target="_blank"
              rel="noopener noreferrer"
              className="flex items-center gap-1.5 px-4 py-2 bg-blue-gray-900 text-white text-sm font-bold rounded-xl hover:bg-blue-gray-700 transition-colors shrink-0 ml-4"
            >
              Buy <ExternalLink className="w-3.5 h-3.5" />
            </a>
          </div>
        ))}

        {swapRecs.length > 0 && (
          <div className="mt-2 pt-4 border-t border-blue-gray-100">
            <p className="text-xs font-bold text-blue-gray-400 uppercase tracking-widest mb-3">Suggested Swaps</p>
            {swapRecs.map((rec) => {
              // For Ashwagandha → Rhodiola swap
              const swapItem = COMPOUND_LINKS["rhodiola"];
              if (!swapItem) return null;
              return (
                <div key={rec.id} className="flex items-center justify-between p-4 rounded-xl border border-blue-100 bg-blue-50 hover:bg-blue-100 transition-colors">
                  <div>
                    <p className="font-bold text-blue-gray-900">{swapItem.name}</p>
                    <p className="text-xs text-blue-gray-500 mt-0.5">{rec.title} • {swapItem.price}</p>
                  </div>
                  <a
                    href={swapItem.link}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="flex items-center gap-1.5 px-4 py-2 bg-blue-600 text-white text-sm font-bold rounded-xl hover:bg-blue-700 transition-colors shrink-0 ml-4"
                  >
                    Buy <ExternalLink className="w-3.5 h-3.5" />
                  </a>
                </div>
              );
            })}
          </div>
        )}
      </div>
    </div>
  );
}
