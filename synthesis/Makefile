.PHONY: install-musescore compress-fmt-synthetic download-fmt-synthetic

install-musescore:
	rm -rf ../data/musescore.AppImage
	wget https://github.com/musescore/MuseScore/releases/download/v3.6.2/MuseScore-3.6.2.548021370-x86_64.AppImage
	mv MuseScore-3.6.2.548021370-x86_64.AppImage ../data/musescore.AppImage
	chmod +x ../data/musescore.AppImage

compress-fmt-synthetic:
	cd ../data && tar -czvf FMT-synthetic.tgz FMT-synthetic/
	cd ../data && split --bytes=1900MB FMT-synthetic.tgz FMT-synthetic.tgz.part_

download-fmt-synthetic:
	rm -rf ../data/FMT-synthetic
	rm -rf ../data/FMT-synthetic.tgz
	rm -rf ../data/FMT-synthetic.tgz.part_*
	cd ../data && wget https://github.com/Jirka-Mayer/synthetic-fmt-ctc/releases/download/datasets/FMT-synthetic.tgz.part_aa
	cd ../data && wget https://github.com/Jirka-Mayer/synthetic-fmt-ctc/releases/download/datasets/FMT-synthetic.tgz.part_ab
	cd ../data && cat FMT-synthetic.tgz.part_* > FMT-synthetic.tgz
	cd ../data && tar -xzvf FMT-synthetic.tgz
