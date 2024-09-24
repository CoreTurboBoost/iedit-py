
# Edit is a mode based graphical image editing tool
Uses python3 with pygame.

Controls:
 - Mouse wheel up, down, zooms in and out.
 - Escape can be used to exit text prompts and return to normal mode.
 - key q, quits the program (In normal mode).
 - key s, select color (In normal mode).
 - key c, set color (In normal mode).
 - key r, resize editing surface (In normal mode).
 - key u, undo editing surface modification (In normal mode).
 - key w, save editing surface (In normal mode).
 - key return, confirm (In any mode, used for prompts).
 - The key's can also be found by running the application with the --key-bindings cli argument.

UI:
 - Top-Right color pallet boxes. The box with a border is the currently selected box.
 - Under that there is RGBA value of the current selected color
 - Under that is the indicator showing the current layer index and the total number of layers ( (current-layer-index)/(total-number-of-layers))
 - Bottom-Left is the current selected mode.
 - Bottom-Right is the text input box. This will automatically show up when in a mode that uses the text input box.
 - Above that is the Error message box. This show the lattest error message, if there are any.
