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

function trainExists() {
	label = document.getElementById('Lblx');
	
	if(label) {
		if(label.innerText == "")
			return true;
		
		return false;
	} else {
		return false; 
	}
}

function pageHasMultipleTables() {
	table = document.getElementById('DetailsView1');
	
	if(table) {
		items = table.getElementsByTagName('a');
		if(items)
			return true;
		
		return false;
	} else {
		return false; 
	}
}

function getTableAndSwap() {
	table = document.getElementById('DetailsView1');
	
	if(table) {
		tableContents = table.outerHTML;
		
		items = table.getElementsByTagName('a');
		if(items)
			items[0].click();
		
		return tableContents;
	} else {
		return false; 
	}
}

function GetTableDate(str) {
	parser = new DOMParser();
    xmlDoc = parser.parseFromString(str, "text/xml");
	date = xmlDoc.getElementsByTagName("caption")[0].textContent.slice(16, 26).split(".");
	return new Date(date[2], date[1] - 1, date[0]);
}

var Table1 = "",
	Table2 = "";
var currentTable = 0;

function parse(time, retry){

    setTimeout(function() {
		var exists = evaluate(page, trainExists);
		if(exists == false) {
			phantom.exit();
		}
		
        var ret = evaluate(page, getTableAndSwap);
		
        if(ret != false) {
			if(currentTable == 0) {
				Table1 = ret;
				currentTable++;
				
				var multiplePages = evaluate(page, pageHasMultipleTables);
				
				if(multiplePages == false) {
					console.log(Table1);
					phantom.exit();
				}
				
				parse(1, 0);
			} else if(currentTable == 1) {
				if(new String(ret).valueOf() == new String(Table1).valueOf()) {
					parse(1, 0);
				} else {
					Table2 = ret;
					
					if(GetTableDate(Table1) > GetTableDate(Table2))
						console.log(Table1);
					else
						console.log(Table2);
					
					phantom.exit();
				}
			}
		} else if (retry != 1) {
			parse(1, 1);
		}
    }, time * 1000);
}

	
id = system.args[1];
url = "http://appiris.infofer.ro/MyTrainRO.aspx?tren=" + id;


page.open(url, function() {
	/*
	  evaluate(page, function(id) {

		document.getElementById('Button2').click();
	  }, id);
	*/

	parse(1,0)
});