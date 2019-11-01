$(document).ready(
	$("#hintBox").hide(),
	$("#result").hide(),
	$("#editForm").hide()
); 

function setMin() {
	$("#end").val("");
	$("#end").attr({
		"min": $("#start").val()
	});
}

$("#ediAmount").change(function() {
	var amount = $("#ediAmount").val();
	if (!amount) {
		$("#toUpdate").removeAttr("disabled");
	}
	else if (amount < 1) {
		alert("最低記帳金額為1元");
		$("#toUpdate").attr("disabled","disabled");
	}
	else {
		$("#toUpdate").removeAttr("disabled");
	}
});

$("#trashIcon").hover(
	function() {
		$(this).css("color","#dc3545");},
	function() {
		$(this).css("color","#6c757d");}
);

$("#filterIcon").hover(
	function() {
		$(this).css("color","#007bff");},
	function() {
		$(this).css("color","#6c757d");}
);

function deleteBill() {
	$.ajax({
		url: "/billDelete",
		type: "POST",
		data: JSON.stringify({"id": trID}),
		contentType: "application/json",
		success: function(result) {
			$("#"+trID).remove();
			trID = null;

			$("#closed").click();

			var newSum = 0;
			$("td[id$=ediAmount]").each(function() {
				newSum += Number($(this).text());
			});
			$("#sum").text(newSum);
		}
	});
}

var trID = null;
$("tbody").on("click", "tr", function() { 
	// if another row is clicked
	if (trID && this.id != trID) {
		var newID = this.id;
		$("#"+trID).css("background-color", "transparent");
		$("#"+newID).css("background-color", "#ffdf80");
		$("#ediDate, #ediGroup, #ediNote, #ediAmount").val("");
		$("#toUpdate").click(newID, function(){
			recordEdit(newID);
		});
		trID = newID;
	}

	trID = this.id;
	$("#"+this.id).css("background-color", "#ffdf80");
	$("#editForm").show("slow");
	$("#ediDate, #ediGroup, #ediNote, #ediAmount").val("");
	$("#toUpdate").click(trID, function(){
		recordEdit(trID);
	});
});

function recordEdit(rowID) {
	// contain the info that should POST to application.py
	var editItem = {};

	// collect <div id="editForm"> data
	$("input[id^='edi'], select[id^='edi']").each(function() {
		var key = $(this).attr('id');
		var value = $(this).val();
		
		if (key == "ediDate" && value) {
			editItem[key] = value.replace(/-/g,"");
		}
		else if (value) {
			editItem[key] = value;
		}
	});

	if ($.isEmptyObject(editItem)) {
		$("#hintText").html("請填入至少一個修改內容，或按下「算了」取消修改");
		$("#hintBox").attr("class","alert alert-info");
		$("#hintBox").show();
	}
	else {
		editItem["id"] = rowID;
		$("#hintBox").hide();
		$("*[id^='edi']").each(function() {
			$(this).val("");
		});

		$.ajax({
			url: "/billEdit",
			type: "POST",
			data: JSON.stringify({"content":editItem}),
			dataType: "json",
			contentType: "application/json; charset=UTF-8",
			success: function(result) {
				if (result == true) {
					$("#hintText").html("更新成功");
					$("#hintBox").attr("class","alert alert-success");
					$("#hintBox").show().delay(1500).fadeOut();
					$("#"+rowID).css("background-color", "transparent");
				}
			}
		});

		// update tr display content(s)
		$.each(editItem, function(key, value){
			if (key == "ediGroup") {
				var displayName = $("option[value="+value+"]").text();
				$("#"+rowID+key).text(displayName);
			}
			else {
				$("#"+rowID+key).text(value);
			}
		});

		// update sum cell in <tfoot>
		var newSum = 0;
		$("td[id$=ediAmount]").each(function() {
			newSum += Number($(this).text());
		});
		$("#sum").text(newSum);
	}
}

// click outside to hide edit table
$(document).click(function(event) {
	var x = $("tr, #editForm, #search, #dialog, div[class^=modal]");
	if (!x.is(event.target) && x.has(event.target).length === 0) {
		cancelEdit();
	}
});

function cancelEdit() {
	$("#"+trID).css("background-color", "transparent");
	$("#editForm").hide("slow");
	$("#hintBox").hide();
}