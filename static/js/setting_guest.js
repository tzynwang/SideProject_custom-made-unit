$("#updateTargets").on("click", function() {
	var targetAmount = $("#targetAmount").val();
	var target = $("#target").val();
	var targetUnit = $("#targetUnit").val();
	if (!targetAmount && !target && !targetUnit) {
		$("#hintT").text("請至少輸入一項更新內容");
		return false
	}
	if (targetAmount && (targetAmount >= 1 || targetAmount < 2147483647)) {
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
	else {
		if (targetAmount) {
			$("#targetAmountSpan").text(targetAmount);
			$("#targetAmount").val("");
		}
		if (target) {
			$("#targetSpan").text(target);
			$("#target").val("");
		}
		if (targetUnit) {
			$("#targetUnitSpan").text(targetUnit);
			$("#targetUnit").val("");
		}
		$("#hintT").text("更新成功").show().delay(3000).fadeOut();
	}
});

$("#updateName").on("click", function() {
	var updateName = $("#groupName").val();
	var selectGroup = $("#groupKey").val();
	var id = $("#groupKey").children(":selected").attr("id");

	if (!updateName || !selectGroup) {
		$("#hintG").text("請選擇組別並輸入欲更新之名稱");
	}
	else {
		$("#hintG").text("分組名稱更新成功").show().delay(3000).fadeOut();
		$("#"+id).text(updateName);
		$("#groupName").val("");
	}
})
