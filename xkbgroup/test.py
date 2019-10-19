import itertools

from ctypes import *

from xkb import *


NOTIFY_NAMES = {
    XkbNewKeyboardNotify: "XkbNewKeyboardNotify",
    XkbMapNotify: "XkbMapNotify",
    XkbStateNotify: "XkbStateNotify",
    XkbControlsNotify: "XkbControlsNotify",
    XkbIndicatorStateNotify: "XkbIndicatorStateNotify",
    XkbIndicatorMapNotify: "XkbIndicatorMapNotify",
    XkbNamesNotify: "XkbNamesNotify",
    XkbCompatMapNotify: "XkbCompatMapNotify",
    XkbBellNotify: "XkbBellNotify",
    XkbActionMessage: "XkbActionMessage",
    XkbAccessXNotify: "XkbAccessXNotify",
    XkbExtensionDeviceNotify: "XkbExtensionDeviceNotify"}

def main():
    XkbIgnoreExtension(False)

    display_name = None
    event_type = c_int()
    major = c_int(XkbMajorVersion)
    minor = c_int(XkbMinorVersion)
    reason = c_int()

    display = XkbOpenDisplay(
        display_name,
        byref(event_type), None, byref(major), byref(minor), byref(reason))
    keyboard_description = XkbGetMap(display, 0, XkbUseCoreKbd)
    status = XkbGetControls(display, XkbAllControlsMask, keyboard_description)
    assert status == Success
    names_mask = XkbSymbolsNameMask | XkbGroupNamesMask
    status = XkbGetNames(display, names_mask, keyboard_description)
    assert status == Success
    #events_mask = XkbStateNotifyMask | XkbMapNotifyMask
    events_mask = XkbAllEventsMask
    status = XkbSelectEvents(display, XkbUseCoreKbd, events_mask, events_mask)
    assert status == True_

    print("Event type: {} ({})".format(event_type, type(event_type)))

    report = XEvent()
    lang = None

    def dump_c_struct(struct):
        for attr in dir(struct):
            if not attr.startswith("_"):
                obj = getattr(struct, attr)
                try:
                    if hasattr(obj, "contents"):
                        print("*p* {:20} -- {}".format(attr, obj))
                        print("*v* {:20} -- {}".format(attr, obj.contents))
                    elif hasattr(obj, "_length_"):
                        print("*a* {:20} -- {} ({})".format(attr, list(obj), obj._length_))
                    else:
                        print("*** {:20} -- {}".format(attr, obj))
                except ValueError as e:
                    print("*n* {:20} -- {}".format(attr, obj))
                    print("!!! {} !!!".format(e))

    def dump_symbols_groups(names):
        symbols = names.symbols
        groups = {i: g for (i, g) in enumerate(names.groups) if g != 0}
        print("symbols: {}\ngroups: {}".format(symbols, groups))
        print("Keyboard description:\n    symbols: {} -- {} ({}),\n    groups: {} -- {} ({})"
            .format(
                symbols, XGetAtomName(display, symbols), type(symbols),
                groups, [XGetAtomName(display, g) for g in groups.values()], type(names.groups)))

    dump_c_struct(keyboard_description.contents)
    print('-' * 80)
    dump_c_struct(keyboard_description.contents.names.contents)
    dump_symbols_groups(keyboard_description.contents.names.contents)

    def callback(event, event_type):
        nonlocal display, lang, keyboard_description
        print("Callback step 1")
        if event.type == event_type.value:
            print("Callback step 2")
            #assert isinstance(event, XkbEvent)
            print("Callback step 3")
            xkb_event = cast(byref(event), POINTER(XkbEvent)).contents
            if xkb_event.any.xkb_type == XkbStateNotify:
                print("Callback step 4 (state)")
                if lang != xkb_event.state.group:
                    lang = xkb_event.state.group
                    print("New layout: {}".format(lang))
            elif xkb_event.any.xkb_type == XkbMapNotify:
                print("Callback step 4 (map)")
                changes = XkbMapChangesRec()
                map_notify_to_changes(changes, xkb_event.map)
                XkbChangeMap(display, keyboard_description, changes)
                print("New map: {}".format(keyboard_description))
            elif xkb_event.any.xkb_type == XkbNewKeyboardNotify:
                print("Callback step 4 (new keyboard)")
                #XkbFreeClientMap(keyboard_description, 0, True)
                #keyboard_description = XkbGetMap(display, 0, XkbUseCoreKbd)
                #XkbGetUpdatedMap(display, 0, keyboard_description)
                XkbFreeNames(keyboard_description, names_mask, True)
                XkbFreeControls(keyboard_description, XkbAllControlsMask, True)
                XkbFreeClientMap(keyboard_description, 0, True)
                XCloseDisplay(display)
                display = XkbOpenDisplay(
                    display_name,
                    byref(event_type), None, byref(major), byref(minor), byref(reason))
                keyboard_description = XkbGetMap(display, 0, XkbUseCoreKbd)
                status = XkbGetControls(display, XkbAllControlsMask, keyboard_description)
                status = XkbGetNames(display, names_mask, keyboard_description)
                status = XkbSelectEvents(display, XkbUseCoreKbd, events_mask, events_mask)
                kbd = keyboard_description.contents
                dump_c_struct(kbd)
                print('-' * 80)
                names_ptr = kbd.names
                names = names_ptr.contents
                dump_c_struct(names)
                dump_symbols_groups(names)
            else:
                print("Callback step 4 (other)")
                xkb_type = xkb_event.any.xkb_type
                print("Other: {} ({})".format(NOTIFY_NAMES[xkb_type], xkb_type))

    for i in itertools.count():
        XNextEvent(display, byref(report))
        print("Step {}".format(i))
        callback(report, event_type)
        print("Event type: {} ({})\n".format(report.type, type(report.type)))

def map_notify_to_changes(changes, map_notify):
    attrs = ["first_type", "num_types", "min_key_code", "max_key_code", "first_key_sym", "first_key_act", "first_key_behavior", "first_key_explicit", "first_modmap_key", "first_vmodmap_key", "num_key_syms", "num_key_acts", "num_key_bahaviors", "num_key_explicit", "num_vmodmap_keys", "num_vmodmap_keys", "vmods"]
    for attr in attrs:
        setattr(changes, attr, getattr(map_notify, attr))


if __name__ == "__main__":
    main()
