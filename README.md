## Restart


This extension adds a "Restart" function to Blender's File menu and via a `Ctrl+Alt+Shift+R` keyboard shortcut. If unsaved changes are detected, a confirmation dialog is displayed to manage how the file is handled before restarting.

### Features

**Primary Functions**

* **File Menu Button:** Adds a `Restart` option to the `File` menu.

* **Keyboard Shortcut:** Adds a `Ctrl+Alt+Shift+R` shortcut to trigger the restart operation. This shortcut can be changed in the native Blender keymaps menu.

**Confirmation Dialog**

When unsaved changes are present, a dialog box appears with the following options:

* **`Save`:** Saves the current file and then restarts. If the file has never been saved, it opens the "Save As..." dialog and restarts after the save is complete.

* **`Don't Save`:** Discards unsaved changes and restarts, reopening the last saved version of the file.

* **`Cancel`:** Closes the dialog and cancels the restart operation.

**Warning System**

* When restarting a file that has not been saved to disk, the filename will be displayed in red.

### Addon Preferences

The addon's default behavior for handling unsaved changes can be configured in the Addon Preferences via the "Restart Behavior" setting.

* **Prompt before Restarting (Default):** Shows the four-button confirmation dialog.

* **Save and Restart:** Automatically saves the file and restarts. If the file is new, the confirmation dialog will be shown instead.

* **Discard and Restart:** Automatically discards unsaved changes and restarts.