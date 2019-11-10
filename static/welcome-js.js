$(
    $("#hintLogin").hide(), // login
    $("#passReset").hide(), // reset password button
    $("#hintRegister").hide() // register
);

$($("#goRegister").on("click", function() {
        $("#register-tab").click();
    })
);

// login: verify username
$("#usernameLogin").on("change", function() {
    $("#passReset").hide();
    var username = $(this).val();
    $.ajax({
        url: "/newUser",
        type: "GET",
        data: {"username": username},
        dataType: "json",
        contentType : "application/json",
        success: function(result){
            if (result == true) {
                $("#hintLogin").show();
                $("#ID").html(username);
                $("#submitLogin").attr("disabled", true);
            }
            else {
                $("#hintLogin").hide();
                $("#submitLogin").attr("disabled", false);
                $("#passReset").show();
            }
        },
    });
});

// register: verify username
$("#usernameRegister").on("change", function() {
    var username = $(this).val();
    $.ajax({
        type: "GET",
        url: "/checkUser",
        data: {"username": username},
        dataType: "json",
        contentType : "application/json",
        success: function(result){
            if (result == "nameContFail") {
                $("#hintRegister").show();
                $("#hintText").html("帳號內容不符合規範");
                $("#submitRegister").attr("disabled", true);
            }
            else if (result == "userExist") {
                $("#hintRegister").show();
                $("#hintText").html("這個帳號名稱已經有人使用過了，請換一個");
                $("#submitRegister").attr("disabled", true);
            }
            else if (result == "lenFail") {
                $("#hintRegister").show();
                $("#hintText").html("帳號長度不符合規範");
                $("#submitRegister").attr("disabled", true);
            }
            else {
                $("#hintRegister").hide();
                $("#submitRegister").attr("disabled", false);
            }
        },
    });
});

// register: verify email
$("#email").on("change", function() {
    var maddress = $(this).val();
    $.ajax({
        type: "GET",
        url: "/mailValidate",
        data: {"maddress": maddress},
        dataType: "json",
        contentType : "application/json",
        success: function(result) {
            if (result == "mailExist") {
                $("#hintRegister").show();
                $("#hintText").html("輸入的email已經被使用過了");
                $("#submitRegister").attr("disabled", true);
            }
            else if (result == "mailFail") {
                $("#hintRegister").show();
                $("#hintText").html("輸入的email無效，請檢查拼字、或是確認這個email的有效性");
                $("#submitRegister").attr("disabled", true);
            }
            else {
                $("#hintRegister").hide();
                $("#submitRegister").attr("disabled", false);
            }
        },
    });
});

// register: verify password
$("#registerForm").submit(function(event){
    event.preventDefault();
    var pass1 = $("#pass1").val();
    var pass2 = $("#pass2").val();

    if (pass1 == pass2) {
        $.ajax({
            url: "/checkPass",
            type: "POST",
            data: JSON.stringify({"pass1": pass1}),
            dataType: "json",
            contentType: "application/json",
            success: function(result) {
                if (result == "nameContFail") {
                    $("#hintRegister").show();
                    $("#hintText").html("密碼內容不符合規範");
                }
                else if (result == "lenFail") {
                    $("#hintRegister").show();
                    $("#hintText").html("密碼長度不符合規範");
                }
                else {
                    $("#hintRegister").hide();
                    $("#registerForm").unbind("submit").submit();
                }
            },
        });
    }
    else {
        $("#hintRegister").show();
        $("#hintText").html("密碼與確認密碼的內容不同");
    }
});