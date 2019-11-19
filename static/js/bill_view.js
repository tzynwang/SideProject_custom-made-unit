$(
	$("#hintBox").hide(),
	$("#dateselector").hide(),
	$("#result").hide(),
	$("#editForm").hide()
);

var today = moment().format(moment.HTML5_FMT.DATE);
var yearago = moment().add(-1, 'y').format(moment.HTML5_FMT.DATE);
$(
	$("#start").attr({
		min: yearago,
		max: today
	})
);

$("input[name='dateSelect']").on("change", function() {
	var pick = $(this).val();
	if (pick == "userselect") {
		$("#dateselector").show();
	}
	else {
		$("#dateselector").hide();
		if (pick == "thisday") {
			$("#start").attr("value", today);
			$("#end").attr("value", today);
		}
		if (pick == "thisweek") {
			var weekstart = moment().startOf('week').format(moment.HTML5_FMT.DATE);
			$("#start").attr("value", weekstart);
			$("#end").attr("value", today);
		}
		if (pick == "thismonth") {
			var monstart = moment().startOf('month').format(moment.HTML5_FMT.DATE);
			$("#start").attr("value", monstart);
			$("#end").attr("value", today);
		}
	}
});

$("#start").on("change", function() {
	var start = $("#start").val();
	var end = $("#end").val();
	if (start > end) {
		$("#end").val("");
		$("#end").attr({
			"min": $("#start").val()
		});
	}
});

function sortRow(index, ID) {
	var tbody = $('#row');
	// find all row(s) in <tbody>, then sort()
	tbody.find("tr").sort(function (a, b) {
		if ($("#"+ID).hasClass("ascend") == true) {
			// get text of the children element with 'index'
			return parseInt($(a).children().eq(index).text()) - parseInt($(b).children().eq(index).text());
		}
		else {
			return parseInt($(b).children().eq(index).text()) - parseInt($(a).children().eq(index).text());
		}
	}).appendTo(tbody); // cut and paste to the end

	$("#"+ID).attr("class");
	$("#"+ID).children().attr("class");
	if ($("#"+ID).hasClass("ascend") == true) {
		$("#"+ID).attr("class", "descend");
		$("#"+ID).children().attr("class", "fas fa-sort-up fa-sm");
	}
	else {
		$("#"+ID).attr("class", "ascend");
		$("#"+ID).children().attr("class", "fas fa-sort-down fa-sm");
	}
}

var tdName = ["null","ediDate","ediGroup","ediNote","ediAmount"];
$("#sendTime").on("click", function() {
	$("#result").val("");
	var start = $("#start").val();
	var end = $("#end").val();

	var selected = [];
	$("div[name='selectedGroup'] input:checked").each(function() {
		selected.push($(this).val());
	});

	if (!start || !end) {
		$("#hintText").html("請設定查詢日期");
		$("#hintBox").attr("class","alert alert-info");
		$("#hintBox").show();
	}
	else if ($.isEmptyObject(selected)) {
		$("#hintText").html("請選擇至少一個帳目分組");
		$("#hintBox").attr("class","alert alert-info");
		$("#hintBox").show();
	}
	else {
		// pull record(s) from server side
		$.ajax({
			url: "/bill/filter",
			type: "POST",
			data: JSON.stringify({"start":start, "end":end}),
			dataType: "json",
			contentType: "application/json",
			success: function(result) {
				if(!result) {
					$("#hintText").html("此日期區間沒有記帳紀錄");
					$("#hintBox").attr("class","alert alert-warning");
					$("#hintBox").show();
				}
				else {
					$("#hintBox").hide();
					$("#row").empty();
					$("#subTotal").empty();
					$("#result").show();
					var billSum = 0;
					// render table of record(s)
					result.forEach(function(element) {
						// element[2] == group, only render the bill with the selected group
						if ($.inArray(element[2],selected) != -1) {
							var row = document.createElement('tr');
							row.setAttribute("id", element[0]); // set <tr> id
							billSum = billSum + element[4];
							for (i = 1; i < element.length; i++) {
								var cell = document.createElement('td');
								cell.setAttribute("id", element[0]+tdName[i]); // set <td> id
								cell.appendChild(document.createTextNode(element[i]));
								row.appendChild(cell);
							}
							document.getElementById("row").appendChild(row);
						}
					});

					var sumRow = document.createElement('tr'); // set tfoot

					var sumMerge = document.createElement('td');
					sumMerge.setAttribute("colspan", 3);
					sumMerge.setAttribute("align", "right");
					sumMerge.appendChild(document.createTextNode("小記："));
					sumRow.appendChild(sumMerge);

					var sumS = document.createElement('td');
					sumS.setAttribute("id", "sum");
					sumS.appendChild(document.createTextNode(billSum));
					sumRow.appendChild(sumS);

					document.getElementById("subTotal").appendChild(sumRow);
				}
			}
		});
	}
});

$("#ediAmount").on("change", function() {
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

$("#deleteBill").on("click", function() {
	$.ajax({
		url: "/bill/delete",
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
});

var trID = null;
$("tbody").on("click", "tr", function() {
	// if another row is clicked
	if (trID && this.id != trID) {
		var newID = this.id;
		$("#"+trID).css("background-color", "transparent");
		$("#"+newID).css("background-color", "#e2e6ea");
		$("#ediDate, #ediGroup, #ediNote, #ediAmount").val("");
		$("#toUpdate").click(newID, function(){
			recordEdit(newID);
		});
		trID = newID;
	}

	trID = this.id;
	$("#"+this.id).css("background-color", "#e2e6ea");
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
			url: "/bill/edit",
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