interface HomeLesson {
  id: string;
  section: string;
  title: string;
  minutes?: number;
  missions?: unknown;
}
interface HomePart {
  title: string;
  desc: string;
  lessons: HomeLesson[];
}

const minutesOf = (lessons: { minutes?: number }[]) =>
  lessons.reduce((total, l) => total + (l.minutes || 0), 0);

function renderParts(root: HTMLElement, parts: HomePart[], done: Set<string>) {
  for (const part of parts) {
    const [num, name] = part.title.split(" · ");
    const finished = part.lessons.filter((l) => done.has(l.id)).length;
    const n = part.lessons.length;
    const card = document.createElement("li");
    card.className = "part";
    card.innerHTML = `<div class="h"><p class="no"></p><h3></h3><p class="d"></p>
      <div class="pr"><progress max="${n}" value="${finished}" aria-label="Lecciones completadas de esta parte"></progress><span class="n">${finished}/${n}</span></div></div>
      <details><summary>${n} lecciones, ${minutesOf(part.lessons)} min</summary></details>`;
    card.querySelector(".no")!.textContent = num;
    card.querySelector("h3")!.textContent = name || num;
    card.querySelector(".d")!.textContent = part.desc;
    const details = card.querySelector("details")!;
    if (
      part.lessons.some((l) => !done.has(l.id)) &&
      part.lessons.some((l) => done.has(l.id))
    )
      details.open = true;
    const list = document.createElement("ul");
    list.className = "lessons";
    for (const l of part.lessons) {
      const li = document.createElement("li");
      const a = document.createElement("a");
      a.href = "lesson.html?l=" + encodeURIComponent(l.id);
      if (done.has(l.id)) a.className = "done";
      const section = document.createElement("span");
      section.className = "s";
      section.textContent = l.section;
      const title = document.createElement("span");
      title.className = "t";
      title.textContent = l.title;
      if (l.missions) {
        const tag = document.createElement("span");
        tag.className = "tag";
        tag.textContent = " con práctica";
        title.append(tag);
      }
      const time = document.createElement("span");
      time.className = "m";
      time.textContent = done.has(l.id) ? "Hecha" : l.minutes + " min";
      a.append(section, title, time);
      li.append(a);
      list.append(li);
    }
    details.append(list);
    root.append(card);
  }
}

window.QGHome = { renderParts, minutesOf };
