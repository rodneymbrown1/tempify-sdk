from typing import List
from templify.core.analysis.detectors.heuristics.heading_detector import HeadingDetection
from templify.core.analysis.utils.pattern_descriptor import PatternDescriptor
from templify.core.analysis.utils.section import Section


def build_sections_from_headings(
    detections: List[HeadingDetection],
    descriptors: List[PatternDescriptor],
    default_group: str = "group0",
) -> List[Section]:
    """
    Build a recursive Section tree from ordered headings.

    Args:
        detections: list of HeadingDetection (ordered by line index).
        descriptors: list of PatternDescriptor aligned 1:1 with detections.
        default_group: layout_group to assign if no override.

    Returns:
        List[Section]: top-level sections with nested subsections.
    """
    root_sections: List[Section] = []
    stack: List[Section] = []  # keeps track of the current path

    for det, desc in zip(detections, descriptors):
        # Create section node via factory
        section = Section.from_heading(det, desc, layout_group=default_group)

        if not stack:  # first heading
            root_sections.append(section)
            stack = [section]
            continue

        prev_level = stack[-1].level or det.level or 1
        curr_level = det.level or 1

        if curr_level > prev_level:
            stack[-1].add_subsection(section)
            stack.append(section)
        elif curr_level == prev_level:
            stack.pop()
            if stack:
                stack[-1].add_subsection(section)
            else:
                root_sections.append(section)
            stack.append(section)
        else:
            # climb back up to correct parent
            while len(stack) > 1 and (stack[-1].level or prev_level) >= curr_level:
                stack.pop()
            if stack:
                stack[-1].add_subsection(section)
            else:
                root_sections.append(section)
            stack.append(section)

    return root_sections
