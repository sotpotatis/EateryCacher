/* editors.js
* Initializes on-page code editors to highlight syntax.
*/
const editors = [{
    id: "menu-response",
    foldLines: [5,22,40,57,75],
    customHeight: "25vh"
}, {
    id: "menu-list-response",
    foldLines: [1]
}, {
    id: "error-response"
}];
for (const editorData of editors) {
    let editorElement = document.getElementById(editorData.id)
    // Commented out: code using Ace editor (switched to CodeMirror)
    /*let editor = ace.edit(editorElement, {
        selectionStyle: "text",
        mode: "ace/mode/json",
        readOnly: true
    })*/
    let editor = CodeMirror.fromTextArea(editorElement, {
        mode: "javascript",
        lineNumbers: true,
        readOnly: true,
        theme: "nord"
    })
    // Set size: either custom or default
    editor.setSize("100%", editorData.customHeight? editorData.customHeight: "15vh")
    // Check if lines should be folded (and if so, fold them)
    if (editorData.foldLines !== undefined){
        for (const lineNumber of editorData.foldLines){
            editor.foldCode(lineNumber)
        }
    }
}