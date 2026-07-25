from pathlib import Path
p=Path(r"C:/Users/zhang/Desktop/mumuvenmo/core/root_setup.py")
s=p.read_text(encoding="utf-8")
mark="        low = "
for=0
for i,line in enumerate(s.splitlines()):
    if line.strip()=="low = \" | \".join(outs).lower()": x
        print("found low at", i+1)
        for j,line2 in enumerate(s.splitlines()[i:i+8], start=i):
            print(j, line2)
        break
print("done")