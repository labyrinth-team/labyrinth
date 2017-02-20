LANGS=ar ca cs de el es eu fa fr it nl pl pt_BR pt_PT ru sv zh_CN

LANG_FOLDERS:=$(addprefix $(localedir)/,$(LANGS))
INST_MO:=$(addsuffix /LC_MESSAGES/labyrinth.mo,$(LANG_FOLDERS))

# Translate to binary message format
%.mo: %.po
	msgfmt -o $@ $<

all-mo: $(LANGS:%=%.mo)

# The installation rule
$(localedir)/%/LC_MESSAGES/labyrinth.mo : %.mo
	install -D -m 644 $< $@

install: all-mo $(INST_MO)

labyrinth.pot:
	xgettext --language=Python --keyword=_ --output=$@ `find ../labyrinth_lib -name "*.py"`
	xgettext --output=$@ --join-existing ../data/labyrinth.glade

update-%-po:
	@echo -n "Updating $*.po"
	@result="`msgmerge -o $*.new.po $*.po labyrinth.pot`"; \
	if $$result; then \
		if cmp $*.po $*.new.po >/dev/null 2>&1; then \
			# No changes - discard the new file \
			rm -f $*.new.po; \
		else \
			# File has changed - new file replaces the old \
			if mv -f $*.new.po $*.po; then \
			:; \
			else \
				echo "msgmerge for $*.po failed: cannot move $*.new.po to $*.po" 1>&2; \
				rm -f $*.new.po; \
				exit 1; \
			fi; \
		fi; \
	else \
		echo "msgmerge for $*.gmo failed!"; \
		rm -f $*.new.po; \
	fi; \

update-po: labyrinth.pot $(LANGS:%=update-%-po)

clean:
	rm -rf *.mo
	rm -rf *.new.po
