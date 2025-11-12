import { useState } from "react";

export default function Keypad({ onEnter }: { onEnter: (_value: number) => void }){
  const [buf, setBuf] = useState("");
  const push = (d: string) => setBuf((b) => (b + d).slice(0, 8));
  const back = () => setBuf((b) => b.slice(0, -1));
  const enter = () => { const v = parseInt(buf || "0", 10); onEnter(v); setBuf(""); };

  const btn = "px-4 py-3 border rounded text-xl";
  return (
    <div className="grid gap-2">
      <input className="border rounded p-2 text-right text-xl" value={buf} readOnly />
      <div className="grid grid-cols-3 gap-2">
        {["1","2","3","4","5","6","7","8","9","0"].map(d=>
          <button key={d} className={btn} onClick={()=>push(d)}>{d}</button>
        )}
        <button className={btn} onClick={back}>←</button>
        <button className={btn + " bg-black text-white"} onClick={enter}>Enter</button>
      </div>
    </div>
  );
}