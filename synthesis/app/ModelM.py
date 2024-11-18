import smashcima as sc
from smashcima.synthesis.page.SimplePageSynthesizer import PageSetup
from smashcima.orchestration.BaseHandwrittenModel import BaseHandwrittenScene


class ModelM(sc.orchestration.BaseHandwrittenModel):
    # rasterization
    DPI = 124.6
    
    # stafflines
    STAFF_LINE_WIDTH = sc.px_to_mm(2, dpi=DPI)
    STAFF_SPACE = sc.px_to_mm(10.75, dpi=DPI)
    STAFF_LINE_COLOR = (0, 0, 0, 105)
    
    # page tilt and positioning
    TILT_ANGLE_DEG = 0.2
    PAGE_SHIFT = sc.px_to_mm(3, dpi=DPI)

    def register_services(self):
        super().register_services()

        # TODO: DBEUG: disable the background texture temporarily
        self.container.interface(
            sc.synthesis.PaperSynthesizer,
            sc.synthesis.SolidColorPaperSynthesizer
        )
    
    def configure_services(self):
        super().configure_services()

        # configure page layout to match the "M" dataset look
        page_synth = self.container.resolve(
            sc.synthesis.SimplePageSynthesizer
        )
        page_synth.page_setup = PageSetup(
            # almost A5 landscape
            size = sc.Vector2(
                sc.px_to_mm(1000, dpi=self.DPI),
                sc.px_to_mm(726, dpi=self.DPI)
            ),
            padding_top=sc.px_to_mm(135, dpi=self.DPI),
            padding_bottom=sc.px_to_mm(130, dpi=self.DPI),
            padding_left=0,
            padding_right=0,
            staff_count=5
        )

        # configure stafflines width and spacing
        stafflines_synth = self.container.resolve(
            sc.synthesis.StafflinesSynthesizer
        )
        assert type(stafflines_synth) is sc.synthesis.NaiveStafflinesSynthesizer
        stafflines_synth.line_width = self.STAFF_LINE_WIDTH
        stafflines_synth.staff_space = self.STAFF_SPACE
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
            .then(sc.Transform.scale(1_000 / 1_024)) \
            .then(sc.Transform.rotateDegCC(
                self.rng.normalvariate(0, self.TILT_ANGLE_DEG)
            )) \
            .then(sc.Transform.translate(
                sc.Vector2(
                    self.rng.normalvariate(0, self.PAGE_SHIFT),
                    self.rng.normalvariate(0, self.PAGE_SHIFT)
                )
            ))

        # the new viewport is 1024x761 pixels in the model DPI
        view_width = sc.px_to_mm(1024, dpi=self.DPI)
        view_height = sc.px_to_mm(761, dpi=self.DPI)
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
        scene.renderer.background_color = (242, 244, 244, 255)

        return scene
