var page = require('webpage').create();
var system = require('system');

function evaluate(page, func) {
    var args = [].slice.call(arguments, 2);
    var fn = "function() { return (" + func.toString() + ").apply(this, " + JSON.stringify(args) + ");}";
    return page.evaluate(fn);
}

function click(el){
    var ev = document.createEvent("MouseEvent");
    ev.initMouseEvent(
        "click",
        true , true,
        window, null,
        0, 0, 0, 0,
        false, false, false, false,
        0, null
    );
    el.dispatchEvent(ev);
}

function parse(time, retry){
    setTimeout(function(){
        var ret = evaluate(page, function() { if(document.getElementById('GridSta')) { return document.getElementById('GridSta').outerHTML; } else { return false; } });
        if(ret!=false){ console.log(ret); phantom.exit(); } else if (retry!=1) { parse(20,1); }
    }, time*1000);
}

url = "http://appiris.infofer.ro/SosPlcRO.aspx";

page.open(url, function() {
  var id = system.args[1];

  evaluate(page, function(id) {
    document.getElementById('DropStPlc').value=id;
    document.getElementById('Button2').click();
  }, id);

  parse(8,0)
  
});