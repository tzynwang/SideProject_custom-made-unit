$("#updateTargets").on("click", function() {
	var targetAmount = $("#targetAmount").val();
	var target = $("#target").val();
	var targetUnit = $("#targetUnit").val();
	if (!targetAmount && !target && !targetUnit) {
		$("#hintT").text("請至少輸入一項更新內容");
		return false
	}
	if (targetAmount && (targetAmount < 1 || targetAmount > 2147483647)) {
		$("#hintT").text("金額至少為1");
		return false
	}
	if (target && target.length > 24) {
		$("#hintT").text("目標物名稱最多24個字");
		return false
	}
	if (targetUnit && targetUnit.length > 8) {
		$("#hintT").text("單位名稱最多8個字");
		return false
	}
	$.ajax({
		url: "/setting/target",
		type: "POST",
		data: JSON.stringify({"targetAmount": targetAmount, "target": target, "targetUnit": targetUnit}),
		dataType: "json",
		contentType : "application/json; charset=UTF-8'",
		success: function (result) {
			if (!result || result == false) {
				$("#hintT").text("更新失敗");
			}
			else {
				if (result["targetAmount"]) {
					$("#targetAmountSpan").text(result["targetAmount"]);
					$("#targetAmount").val("");
				}
				if (result["target"]) {
					$("#targetSpan").text(result["target"]);
					$("#target").val("");
				}
				if (result["targetUnit"]) {
					$("#targetUnitSpan").text(result["targetUnit"]);
					$("#targetUnit").val("");
				}
				$("#hintT").text("更新成功").show().delay(3000).fadeOut();
			}
		}
	});
});

$("#updateName").on("click", function() {
	var updateName = $("#groupName").val();
	var selectGroup = $("#groupKey").val();
	if (!updateName || !selectGroup) {
		$("#hintG").text("請選擇組別並輸入欲更新之名稱");
	}
	else {
		$("#hintG").text("");
		$.ajax({
			url: "/setting/group",
			type: "POST",
			data: JSON.stringify({"groupKey": selectGroup, "updateName": updateName}),
			dataType: "json",
			contentType : "application/json; charset=UTF-8'",
			success: function(result) {
				if (result == false) {
					$("#hintG").text("分組名稱更新失敗").show().delay(3000).fadeOut();
				}
				else {
					$("#hintG").text("分組名稱更新成功").show().delay(3000).fadeOut();
					for (i = 0; i < 4; i ++) {
						$("#op"+i).text(result[i]);
					}
					$("#groupName").val("");
				}
			},
		});
	}
})

$("#updatePass").on("click", function() {
	var pass1 = $('#pass1').val();
	var pass2 = $('#pass2').val();
	if (!pass1 || !pass2) {
		$("#hintP").text("請輸入密碼與確認密碼");
	}
	else if (pass1 != pass2) {
		$("#hintP").text("密碼與確認密碼的內容不同");
	}
	else if (pass1 == pass2) {
		$.ajax({
			url: "/check/pass",
			type: "POST",
			data: JSON.stringify({"pass1": pass1}),
			dataType: "json",
			contentType : "application/json",
			success: function(result) {
				if (result == "nameContFail") {
					$("#hintP").text("密碼內容不符合規範");
				}
				if (result == "lenFail") {
					$("#hintP").text("密碼長度不符合規範");
				}
				if (result == true) {
					$.ajax({
						url: "/setting/account/pass",
						type: "POST",
						data: JSON.stringify({"pass1": pass1}),
						dataType: "json",
						contentType : "application/json",
						success: function() {
							$('#pass1').val("");
							$('#pass2').val("");

							$("#hintP").text("密碼更新成功").show().delay(3000).fadeOut();
						},
						error: function() {
							$("#hintP").text("密碼更新失敗").show().delay(3000).fadeOut();
						}
					});
				}
			},
		});
	}
});

$("#updateEmail").on("click", function() {
	var email = $("#email").val();
	if (email) {
		$.ajax({
			type: "GET",
			url: "/check/mail",
			data: {"email": email},
			dataType: "json",
			contentType: "application/json",
			success: function(result) {
				if (result == "mailExist") {
					$("#hintemail").html("輸入的email已經被使用過了");
					return false;
				}
				else if (result == "mailFail") {
					$("#hintemail").html("輸入的email無效，請檢查拼字、或確認email的有效性");
					return false
				}
				else if (result == true) {
					$("#hintemail").html("");
					$.ajax({
						type: "POST",
						url: "/setting/account/email",
						data: JSON.stringify({"email": email}),
						dataType: "json",
						contentType: "application/json",
						success: function() {
							$("#hintE").text("email更新成功").show().delay(3000).fadeOut();
							$("#email").val("");
							$("#emailSpan").text(email);
						},
						error: function() {
							$("#hintE").text("email更新失敗").show().delay(3000).fadeOut();
						}
					});
				}
			},
		});
	}
	else {
		$("#hintemail").html("請輸入email");
		$("#updateEmail").attr("disabled", true);
	}
});