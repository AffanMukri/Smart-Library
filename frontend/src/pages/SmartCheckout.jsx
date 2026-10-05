import { useEffect, useRef, useState } from "react";
import { Camera, CheckCircle2, LoaderCircle, ScanLine } from "lucide-react";
import PageHeader from "../components/PageHeader"; import StatusBadge from "../components/StatusBadge";
import { identifyBook, identifyStudent, issueLoan } from "../services/api"; import { useLibrary } from "../hooks/useLibrary";

export default function SmartCheckout(){
 const video=useRef(null), stream=useRef(null); const {refresh}=useLibrary();
 const [cameraError,setCameraError]=useState(""),[busy,setBusy]=useState(false),[message,setMessage]=useState(""),[confidence,setConfidence]=useState(null);
 const [studentText,setStudentText]=useState("23IT101"),[bookText,setBookText]=useState("BOOK001"),[student,setStudent]=useState(null),[book,setBook]=useState(null),[success,setSuccess]=useState(null);
 useEffect(()=>()=>stream.current?.getTracks().forEach(t=>t.stop()),[]);
 async function startCamera(){try{stream.current?.getTracks().forEach(t=>t.stop());stream.current=await navigator.mediaDevices.getUserMedia({video:{facingMode:{ideal:"environment"}},audio:false});video.current.srcObject=stream.current;setCameraError("");}catch(e){setCameraError(e.name==="NotAllowedError"?"Camera permission was denied. Allow access or use manual entry.":"Camera is unavailable. Use manual entry.");}}
 function snapshot(){const canvas=document.createElement("canvas");canvas.width=video.current.videoWidth||1280;canvas.height=video.current.videoHeight||720;canvas.getContext("2d").drawImage(video.current,0,0);return canvas;}
 async function ocr(mode){if(!stream.current){setCameraError("Start the camera before capturing.");return;}setBusy(true);setMessage("Reading image…");try{const {recognize}=await import("tesseract.js");const result=await recognize(snapshot(),"eng");const text=result.data.text.trim();setConfidence(Math.round(result.data.confidence));if(mode==="student"){setStudentText(text);await findStudent(text,result.data.confidence);}else{const code=(text.match(/BOOK\s*\d{3,}/i)?.[0]||text.match(/97[89]\d{10}/)?.[0]||text).replace(/\s/g,"");setBookText(code);await findBook(code);}}catch(e){setMessage(e.message||"OCR failed. Use manual correction.");}finally{setBusy(false);}}
 async function barcode(mode="book"){
  if(!stream.current){setCameraError("Start the camera before scanning.");return;}
  setBusy(true);setMessage(`Scanning ${mode} QR code… Hold it steady inside the camera view.`);
  let unexpected="";
  try{
   const {BrowserMultiFormatReader,BrowserQRCodeReader}=await import("@zxing/browser");
   const qrReader=new BrowserQRCodeReader(), multiReader=mode==="book"?new BrowserMultiFormatReader():null;
   for(let attempt=0;attempt<14;attempt+=1){
    const frame=snapshot();let raw="";
    try{raw=qrReader.decodeFromCanvas(frame).getText();}catch{if(multiReader){try{raw=multiReader.decodeFromCanvas(frame).getText();}catch{/* try the next camera frame */}}}
    if(raw){
     const trimmed=raw.trim();
     if(mode==="student"){
      const value=trimmed.toUpperCase();
      if(/^\d{2}[A-Z]{2,4}\d{3,6}$/.test(value)){setStudentText(value);await findStudent(value,100);return;}
      unexpected=trimmed;
     }else{
      const upper=trimmed.toUpperCase(), isbn=trimmed.replace(/[\s-]/g,"");
      const value=/^BOOK\d{3,}$/.test(upper)?upper:/^(?:\d{10}|\d{13})$/.test(isbn)?isbn:"";
      if(value){setBookText(value);await findBook(value);return;}
      unexpected=trimmed;
     }
    }
    await new Promise(resolve=>setTimeout(resolve,250));
   }
   setMessage(unexpected?`Detected “${unexpected}”, but it is not a valid ${mode} identifier. Use the matching Smart Library QR label.`:`No ${mode} QR code was found. Move it closer, avoid glare, and try again.`);
  }catch(e){setMessage(`Scanner error: ${e.message}. You can still enter the ID manually.`);}finally{setBusy(false);}
 }
 async function findStudent(text=studentText,score=confidence){setBusy(true);setMessage("");try{setStudent(await identifyStudent(text,score));}catch(e){setStudent(null);setMessage(e.message);}finally{setBusy(false);}}
 async function findBook(code=bookText){setBusy(true);setMessage("");try{setBook(await identifyBook(code.trim()));}catch(e){setBook(null);setMessage(e.message);}finally{setBusy(false);}}
 const checks=[{label:"Student exists",ok:!!student},{label:"Student active",ok:student?.status==="ACTIVE"&&!student?.blocked},{label:"Book exists",ok:!!book},{label:"Book available",ok:book?.status==="AVAILABLE"},{label:"Borrowing limit OK",ok:student?student.active_loans<student.borrowing_limit:false}]; const eligible=checks.every(x=>x.ok);
 async function issue(){if(!eligible)return;setBusy(true);try{const result=await issueLoan(student.student_code,book.book_code);setSuccess(result);await refresh();}catch(e){setMessage(e.message);}finally{setBusy(false);}}
 function reset(){setStudent(null);setBook(null);setSuccess(null);setConfidence(null);setMessage("");}
 if(success)return <div><PageHeader eyebrow="Smart checkout" title="Book issued successfully" description="The transaction is stored and the LCD simulator state has been updated."/><section className="mx-auto max-w-2xl rounded-2xl border border-emerald-200 bg-white p-8 shadow-sm"><CheckCircle2 className="text-emerald-500" size={48}/><h3 className="mt-4 text-2xl font-bold text-slate-900">BOOK ISSUED SUCCESSFULLY</h3><dl className="mt-6 grid gap-4 sm:grid-cols-2">{[["Student",success.student],["Book",success.book],["Issue date",new Date(success.issued_at).toLocaleString()],["Due date",new Date(success.due_at).toLocaleDateString()]].map(([k,v])=><div key={k} className="rounded-xl bg-slate-50 p-4"><dt className="text-xs uppercase text-slate-400">{k}</dt><dd className="mt-1 font-semibold text-slate-800">{v}</dd></div>)}</dl><button onClick={reset} className="mt-6 rounded-xl bg-library-600 px-5 py-3 text-sm font-bold text-white">New checkout</button></section></div>;
 return <div><PageHeader eyebrow="Web camera workflow" title="Smart checkout" description="Identify a student, scan a book, validate eligibility, and issue it."/><div className="mb-5 flex items-center gap-2"><StatusBadge>WEB CAMERA</StatusBadge><span className="text-xs text-slate-500">OCR and barcode scanning run in the browser; this is not Arduino camera hardware.</span></div>
 <section className="grid gap-5 xl:grid-cols-[.9fr_1.1fr]"><div className="rounded-2xl border bg-white p-5"><div className="relative aspect-video overflow-hidden rounded-xl bg-slate-950"><video ref={video} autoPlay playsInline muted className="h-full w-full object-cover"/><div className="pointer-events-none absolute inset-1/2 h-48 w-48 -translate-x-1/2 -translate-y-1/2 rounded-2xl border-2 border-white/80 shadow-[0_0_0_999px_rgba(0,0,0,.2)]"/></div><p className="mt-3 text-xs text-slate-500">Place one QR code inside the square, keep it flat, and avoid glare.</p><button onClick={startCamera} className="mt-3 flex items-center gap-2 rounded-xl bg-slate-900 px-4 py-2.5 text-sm font-bold text-white"><Camera size={17}/>Enable camera</button>{cameraError&&<p className="mt-3 rounded-lg bg-amber-50 p-3 text-sm text-amber-800">{cameraError}</p>}</div>
 <div className="space-y-5"><Step number="1" title="Identify student"><Entry value={studentText} setValue={setStudentText} action={()=>findStudent()} label="Student ID or OCR text" button="Find student"/><div className="mt-3 flex flex-wrap gap-2"><Action onClick={()=>barcode("student")} busy={busy}><ScanLine size={16}/>Scan student QR</Action><Action onClick={()=>ocr("student")} busy={busy}>Capture & OCR ID</Action>{confidence!=null&&<span className="self-center text-xs text-slate-500">OCR confidence: {confidence}%</span>}</div>{student&&<Result title="Student verified" rows={[["Name",student.name],["Student ID",student.student_code],["Department",student.department],["Active loans",student.active_loans],["Outstanding fine",`₹${student.outstanding_fine}`]]}/>}</Step>
 <Step number="2" title="Scan book"><Entry value={bookText} setValue={setBookText} action={()=>findBook()} label="Book code or ISBN" button="Find book"/><div className="mt-3 flex flex-wrap gap-2"><Action onClick={()=>barcode("book")} busy={busy}><ScanLine size={16}/>Scan book QR/barcode</Action><Action onClick={()=>ocr("book")} busy={busy}>OCR fallback</Action></div>{book&&<div className="mt-4 flex gap-3"><div className="grid h-24 w-16 shrink-0 place-items-center overflow-hidden rounded-lg bg-slate-100 text-center text-[10px] text-slate-400">{book.cover_url?<img src={book.cover_url} alt="Book cover" className="h-full w-full object-cover"/>:"Cover unavailable"}</div><div className="min-w-0 flex-1"><Result title={book.title} rows={[["Book ID",book.book_code],["ISBN",book.isbn||"—"],["Author",book.author],["Shelf",book.shelf_code],["Availability",book.status]]}/></div></div>}</Step>
 <Step number="3" title="Eligibility check"><div className="space-y-2">{checks.map(x=><div key={x.label} className={`flex items-center gap-2 rounded-lg px-3 py-2 text-sm ${x.ok?"bg-emerald-50 text-emerald-700":"bg-slate-50 text-slate-500"}`}><CheckCircle2 size={16}/>{x.label}</div>)}</div><button disabled={!eligible||busy} onClick={issue} className="mt-4 w-full rounded-xl bg-library-600 px-4 py-3 font-bold text-white disabled:cursor-not-allowed disabled:opacity-40">{busy?<LoaderCircle className="mx-auto animate-spin"/>:"Issue book"}</button></Step></div></section>{message&&<p role="alert" className="mt-5 rounded-xl border border-red-200 bg-red-50 p-4 text-sm text-red-700">{message}</p>}</div>
}
function Step({number,title,children}){return <section className="rounded-2xl border border-slate-200 bg-white p-5"><div className="mb-4 flex items-center gap-3"><span className="grid size-8 place-items-center rounded-full bg-indigo-50 text-sm font-bold text-library-700">{number}</span><h3 className="font-bold text-slate-900">{title}</h3></div>{children}</section>}
function Entry({value,setValue,action,label,button}){return <div className="flex gap-2"><input aria-label={label} value={value} onChange={e=>setValue(e.target.value)} className="min-w-0 flex-1 rounded-xl border border-slate-200 px-3 py-2.5 text-sm outline-none focus:border-indigo-400" placeholder={label}/><button onClick={action} className="rounded-xl border border-indigo-200 bg-indigo-50 px-4 text-sm font-semibold text-library-700">{button}</button></div>}
function Action({children,onClick,busy}){return <button disabled={busy} onClick={onClick} className="flex items-center gap-2 rounded-lg border border-slate-200 px-3 py-2 text-xs font-semibold text-slate-600 disabled:opacity-50">{children}</button>}
function Result({title,rows}){return <div className="mt-4 rounded-xl border border-emerald-200 bg-emerald-50/60 p-4"><p className="font-bold text-emerald-800">{title}</p><dl className="mt-3 grid gap-2 sm:grid-cols-2">{rows.map(([k,v])=><div key={k}><dt className="text-[10px] uppercase text-slate-400">{k}</dt><dd className="text-sm font-semibold text-slate-700">{v}</dd></div>)}</dl></div>}
