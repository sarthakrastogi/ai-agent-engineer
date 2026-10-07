"""Structural tests for the pack's cross-references."""
import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
ROUTER = ROOT / "skills" / "agent-engineer" / "SKILL.md"


def headings(skill: str) -> set:
    out = set()
    for md in (ROOT / "skills" / skill).rglob("*.md"):
        out.update(h.strip().lower() for h in re.findall(r"^#+\s+(.+)$", md.read_text(), re.M))
    return out


class RouterPointers(unittest.TestCase):
    def test_router_section_pointers_exist(self):
        """`agent-x` → *Section name* in the router must match a heading in that skill."""
        text = ROUTER.read_text()
        pairs = re.findall(r"`(agent-[a-z-]+)` → \*([^*]+)\*", text)
        self.assertTrue(pairs, "router has no section pointers")
        for skill, section in pairs:
            with self.subTest(skill=skill, section=section):
                self.assertIn(section.strip().lower(), headings(skill))

    def test_router_asset_pointers_exist(self):
        for asset in set(re.findall(r"`assets/([\w.-]+)`", ROUTER.read_text())):
            with self.subTest(asset=asset):
                self.assertTrue((ROUTER.parent / "assets" / asset).is_file())

    def test_every_skill_and_agent_mentioned_exists(self):
        skills = {p.name for p in (ROOT / "skills").iterdir() if p.is_dir()}
        agents = {p.stem for p in (ROOT / "agents").glob("*.md")}
        for md in list((ROOT / "skills").rglob("*.md")) + list((ROOT / "agents").glob("*.md")):
            for name in set(re.findall(r"`(agent-[a-z-]+)`", md.read_text())):
                with self.subTest(file=str(md.relative_to(ROOT)), name=name):
                    self.assertIn(name, skills | agents)



class ReferencePointers(unittest.TestCase):
    def test_reference_pointers_resolve(self):
        """`references/x.md` mentioned in a skill exists in that skill (or the named skill)."""
        skills_dir = ROOT / "skills"
        files = list(skills_dir.rglob("*.md")) + list((ROOT / "agents").glob("*.md"))
        for md in files:
            text = md.read_text()
            own = md.relative_to(skills_dir).parts[0] if skills_dir in md.parents else None
            for m in re.finditer(r"(?:`(agent-[a-z-]+)`\s*(?:→|->|skill's)\s*)?`?references/([\w.-]+\.md)`?", text):
                skill = m.group(1) or own
                if skill is None:
                    continue
                with self.subTest(file=str(md.relative_to(ROOT)), ref=f"{skill}/{m.group(2)}"):
                    self.assertTrue((skills_dir / skill / "references" / m.group(2)).is_file())


if __name__ == "__main__":
    unittest.main()
