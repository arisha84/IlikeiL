// remove
function RemoveValidate()
{
	if(document.getElementById('QuickValidate'))
	{
		var QuickValidate = document.getElementById('QuickValidate');
		QuickValidate.parentNode.removeChild(QuickValidate);
	}
}

// update
function UpdateValidate(list)
{
	document.getElementById('QuickValidate-Content').innerHTML = list;
}

RemoveValidate();

// create overlay
var overlay	= "<div id='QuickValidate' align='middle' style='position:fixed;top:0;width:100%;height:270px;margin:0 auto;text-align:center;z-index:9000;'><div id='QuickValidate-Blocker' style='position:absolute;width:750px;-moz-border-radius:0 0 10px 10px;-webkit-border-radius:0 0 10px 10px;border:solid 3px #FFFFFF;background:#0000AA;opacity:.75;filter:alpha(opacity=75);-moz-opacity:0.75;height:270px;z-index:9001;'></div><div id='QuickValidate-Holder' style='position:absolute;width:740px;padding:10px;z-index:9002;height:230px;overflow:none;color:#FFFFFF;font-family:Arial;'><h1 style='font-size:30px;float:left;padding:0;margin:0 0 10px 0;color:#FFFFFF;'>Suggest this to iLike-IL</h1><button style='float:right;' onclick='RemoveValidate();'>x</button><div id='QuickValidate-Content' style='clear:both;padding:10px 0;border-top:1px dotted #FFFFFF;z-index:9002;'><iframe src='http://israel-like.appspot.com/addarticle?min=y&url=" + escape(window.location) + "' style='height:205px;width:740px;border:0;'></iframe></div></div></div>";

document.body.innerHTML += overlay;


//javascript:(function(){var%20l='http:'+'//'+'israel-like.appspot.com/static/bkmrklt.js';var%20n=document.createElement('script');n.setAttribute('language','JavaScript');n.setAttribute('src',l);document.body.appendChild(n);})()