$(document).ready(
	$("#hintBox").hide()
);

function updateTargets(updateID) {
	var t = $("#"+updateID).val();
	if (!t) {
		$("#hintBox").attr("class");
		$("#hintBox").attr("class", "alert alert-warning").show();
		$("#hintText").html("請輸入內容");
	}
	else if (updateID == 'targetAmount' && (t < 1 || t > 2147483647)) {
		$("#hintBox").attr("class");
		$("#hintBox").attr("class", "alert alert-warning").show();
		$("#hintText").html("目標金額至少為1");
	}
	else if (updateID == 'target' && t.length > 24) {
		$("#hintBox").attr("class");
		$("#hintBox").attr("class", "alert alert-warning").show();
		$("#hintText").html("目標最多24個字");
	}
	else if (updateID == 'targetUnit' && t.length > 8) {
		$("#hintBox").attr("class");
		$("#hintBox").attr("class", "alert alert-warning").show();
		$("#hintText").html("單位最多8個字");
	}
	else {
		$("#hintBox").hide();
		$.ajax({
			url: "/updateTarget",
			type: "POST",
			data: JSON.stringify({"tType": updateID, "content": t}),
			dataType: "json",
			contentType : "application/json; charset=UTF-8'",
			success: function (result) {
				$("#hintBox").attr("class");
				$("#hintText").html("更新成功");
				$("#hintBox").attr("class", "alert alert-success").show().delay(3000).fadeOut();
				
				$("#"+updateID).val("");
				$("#"+updateID+"Span").html(result);
			}
		});
	}
}

function updateName() {
	var updateName = $("#updateName").val();
	var selectGroup = $("#gNames").val();

	if (!updateName || !selectGroup) {
		$("#hintBox").attr("class");
		$("#hintBox").attr("class", "alert alert-warning").show();
		$("#hintText").html("請選擇組別並輸入欲更新之名稱");
	}
	else {
		$("#hintBox").hide();
		$.ajax({
			url: "/updateGroupName",
			type: "POST",
			data: JSON.stringify({"gNames": selectGroup, "updateName": updateName}),
			dataType: "json",
			contentType : "application/json; charset=UTF-8'",
			success: function(result) {
				if (result == false) {
					$("#hintText").html("分組名稱更新失敗");
					$("#hintBox").attr("class");
					$("#hintBox").attr("class", "alert alert-danger").show().delay(3000).fadeOut();
				}
				else {                           
					$("#hintText").html("分組名稱更新成功");
					$("#hintBox").attr("class");
					$("#hintBox").attr("class", "alert alert-success").show().delay(3000).fadeOut();
					
					for (i = 0; i < 4; i ++) {
						$("#op"+i).text(result[i]);
					}
					
					$("#updateName").val("");
				}  
			},
		});
	}
}

function updatePass() {
	var pass1 = $('#pass1').val();
	var pass2 = $('#pass2').val();
	if (!pass1 || !pass2) {
		$("#hintBox").attr("class");
		$("#hintBox").attr("class", "alert alert-success").show();
		$("#hintText").html("請輸入密碼與確認密碼");
	}
	else if (pass1 != pass2) { 
		$("#hintBox").attr("class");
		$("#hintBox").attr("class", "alert alert-success").show();
		$("#hintText").html("密碼與確認密碼的內容不同");
	}
	else if (pass1 == pass2) {
		$("#hintBox").hide();
		$.ajax({
			url: "/checkPass",
			type: "POST",
			data: JSON.stringify({"pass1": pass1}),
			dataType: "json",
			contentType : "application/json",
			success: function(result) {
				if (result == "nameContFail") {
					$("#hintBox").attr("class");
					$("#hintBox").attr("class", "alert alert-success").show();
					$("#hintText").html("密碼內容不符合規範");
				}
				if (result == "lenFail") {
					$("#hintBox").attr("class");
					$("#hintBox").attr("class", "alert alert-success").show();
					$("#hintText").html("密碼長度不符合規範");
				}
				if (result == true) {
					$("#hintBox").hide();
					$.ajax({
						url: "/updatePass",
						type: "POST",
						data: JSON.stringify({"pass1": pass1}),
						dataType: "json",
						contentType : "application/json",
						success: function() {
							$('#pass1').val("");
							$('#pass2').val("");
							
							$("#hintText").html("密碼更新成功");
							$("#hintBox").attr("class");
							$("#hintBox").attr("class", "alert alert-success").show().delay(3000).fadeOut();
						},
						error: function() {
							$("#hintText").html("密碼更新失敗");
							$("#hintBox").attr("class");
							$("#hintBox").attr("class", "alert alert-danger").show().delay(3000).fadeOut();
						}
					});
				}
			},
		});
	}
}