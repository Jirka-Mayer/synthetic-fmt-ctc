import random

import smashcima as sc
from smashcima.orchestration.BaseHandwrittenModel import BaseHandwrittenScene
from smashcima.synthesis.page.SimplePageSynthesizer import PageSetup


class ModelC(sc.orchestration.BaseHandwrittenModel):
    # rasterization
    DPI = 365
    
    # stafflines
    STAFF_LINE_THICKNESS = sc.px_to_mm(7, dpi=DPI)
    STAFF_SPACE_UNIT = sc.px_to_mm(30.75, dpi=DPI)
    STAFF_LINE_COLOR = (0, 0, 0, 105)
    
    # page tilt and positioning
    TILT_ANGLE_DEG = 0.2
    PAGE_SHIFT = sc.px_to_mm(9, dpi=DPI)

    def __init__(self, rng: random.Random):
        self._rng = rng
        super().__init__()

    def register_services(self):
        super().register_services()

        # use the externally-given RNG
        self.container.instance(random.Random, self._rng)

        # TODO: DBEUG: disable the background texture temporarily
        paper_synth = sc.synthesis.SolidColorPaperSynthesizer()
        paper_synth.color = (246, 239, 244, 255)
        paper_synth.dpi = self.DPI
        self.container.instance(
            sc.synthesis.PaperSynthesizer,
            paper_synth
        )
    
    def configure_services(self):
        super().configure_services()

        # configure page layout to match the "M" dataset look
        page_synth = self.container.resolve(
            sc.synthesis.SimplePageSynthesizer
        )
        page_synth.page_setup = PageSetup(
            # A4 portrait
            size = sc.Vector2(210, 297),
            padding_top=sc.px_to_mm(266, dpi=self.DPI),
            padding_bottom=sc.px_to_mm(303, dpi=self.DPI),
            padding_left=sc.px_to_mm(200, dpi=self.DPI),
            padding_right=sc.px_to_mm(200, dpi=self.DPI),
            staff_count=12
        )

        # configure stafflines width and spacing
        stafflines_synth = self.container.resolve(
            sc.synthesis.StafflinesSynthesizer
        )
        assert type(stafflines_synth) is sc.synthesis.NaiveStafflinesSynthesizer
        stafflines_synth.line_thickness = self.STAFF_LINE_THICKNESS
        stafflines_synth.staff_space_unit = self.STAFF_SPACE_UNIT
        stafflines_synth.line_color = self.STAFF_LINE_COLOR

        # configure music layouting
        self.layout_synthesizer.stretch_out_columns = True
        self.layout_synthesizer.respect_line_and_page_breaks = True
        # self.layout_synthesizer.disable_wrapping = False

    def call(self, score: sc.Score) -> BaseHandwrittenScene:
        scene = super().call(score)
        assert len(scene.pages) == 1, "Expected only one page"
        page = scene.pages[0]

        # wrap the page in another space that zooms out the page a little
        original_page_space = page.space
        zoomed_out_space = sc.AffineSpace()
        page.space = zoomed_out_space
        original_page_space.parent_space = zoomed_out_space

        # center the page on origin and scale down, tilt, and shift
        original_page_space.transform = sc.Transform.translate(
            sc.Vector2(
                -page.view_box.rectangle.width / 2,
                -page.view_box.rectangle.height / 2
            )
        ) \
            .then(sc.Transform.scale(3_000 / 3_300)) \
            .then(sc.Transform.rotateDegCC(
                self.rng.normalvariate(0, self.TILT_ANGLE_DEG)
            )) \
            .then(sc.Transform.translate(
                sc.Vector2(
                    self.rng.normalvariate(0, self.PAGE_SHIFT),
                    self.rng.normalvariate(0, self.PAGE_SHIFT)
                )
            ))

        # the new viewport is 3_298x4_462 pixels in the model DPI
        view_width = sc.px_to_mm(3_298, dpi=self.DPI)
        view_height = sc.px_to_mm(4_462, dpi=self.DPI)
        view_box = sc.ViewBox(
            space=zoomed_out_space,
            rectangle=sc.Rectangle(
                -view_width / 2,
                -view_height / 2,
                view_width,
                view_height
            )
        )
        page.view_box = view_box

        # set the scene renderrer properties
        scene.renderer.dpi = self.DPI
        scene.renderer.background_color = (86, 78, 79, 255)

        return scene
