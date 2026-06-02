#!/usr/bin/env python3
# HS-30-09: WCAG 2.1 contrast check for the Signal palette (tokens.css).
def lin(c):
    c/=255
    return c/12.92 if c<=0.03928 else ((c+0.055)/1.055)**2.4
def L(h):
    h=h.lstrip('#'); r,g,b=(int(h[i:i+2],16) for i in (0,2,4))
    return 0.2126*lin(r)+0.7152*lin(g)+0.0722*lin(b)
def ratio(a,b):
    la,lb=L(a),L(b); return (max(la,lb)+0.05)/(min(la,lb)+0.05)
if __name__=="__main__":
    bg,s1,s2="#0E0F13","#15171D","#1C1F27"
    checks=[("text on bg","#F2F3F5",bg,4.5),("text-muted on bg","#9BA2B0",bg,4.5),
        ("text-faint on bg (meta)","#767E8D",bg,3.0),("accent on bg","#FF6B35",bg,4.5),
        ("ok on bg","#34D399",bg,4.5),("warn on bg","#FBBF24",bg,4.5),
        ("danger on bg","#F87171",bg,4.5),("info on bg","#56C7F5",bg,4.5),
        ("text-muted on surface-2","#9BA2B0",s2,4.5),
        ("dark ink on accent (primary)","#0E0F13","#FF6B35",4.5),
        ("white on danger-fill","#FFFFFF","#DC2626",4.5)]
    ok=True
    for label,fg,b,need in checks:
        r=ratio(fg,b); p=r>=need; ok=ok and p
        print(f"{label:34} {r:6.2f}  {'PASS' if p else 'FAIL'} (need {need})")
    print("ALL PASS" if ok else "FAILURES PRESENT")
