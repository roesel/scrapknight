//plugin bootstrap minus and plus
//http://jsfiddle.net/laelitenetwork/puJ6G/
$('#out_table').on('click', 'button.btn-number', function(e){
    e.preventDefault();

    fieldName = $(this).attr('data-field');
    type      = $(this).attr('data-type');
    var input = $("input[name='count'][data-field='"+fieldName+"']");
    var currentVal = parseInt(input.val());
    if (!isNaN(currentVal)) {
        if(type == 'minus') {

            var plusbtn = $("button.btn-number[data-type='plus'][data-field='"+fieldName+"']");
            plusbtn.prop('disabled', false);

            if(currentVal > input.attr('min')) {
                input.val(currentVal - 1).change();
            }
            if(parseInt(input.val()) == input.attr('min')) {
                $(this).prop('disabled', true);
            } else {
                $(this).prop('disabled', false);
            }

        } else if(type == 'plus') {

            var minusbtn = $("button.btn-number[data-type='minus'][data-field='"+fieldName+"']");
            minusbtn.prop('disabled', false);

            if(currentVal < input.attr('max')) {
                input.val(currentVal + 1).change();
            }
            if(parseInt(input.val()) == input.attr('max')) {
                $(this).prop('disabled', true);
            } else {
                $(this).prop('disabled', false);
            }

        }
    } else {
        input.val(0);
    }
});
$('.input-number').focusin(function(){
   $(this).data('oldValue', $(this).val());
});
$('#out_table').on('change', '.input-number', function() {

    minValue =  parseInt($(this).attr('min'));
    maxValue =  parseInt($(this).attr('max'));
    valueCurrent = parseInt($(this).val());

    df = $(this).attr('data-field');
    if(valueCurrent >= minValue) {
        $(".btn-number[data-type='minus'][data-field='"+df+"']").removeAttr('disabled')
    } else {
        //alert('Sorry, the minimum value was reached');
        $(this).val($(this).data('oldValue'));
    }
    if(valueCurrent <= maxValue) {
        $(".btn-number[data-type='plus'][data-field='"+df+"']").removeAttr('disabled')
    } else {
        //alert('Sorry, the maximum value was reached');
        $(this).val($(this).data('oldValue'));
    }

    var price = $("#out_table").find("span[name='price'][data-field='"+df+"']");
    var multiprice = $("#out_table").find("span[name='multiprice'][data-field='"+df+"']");

    valueCurrent = parseInt($(this).val());
    priceCurrent = parseInt(price.text());
    multipriceOld = parseInt(multiprice.text());

    if (multipriceOld > 0) {
    } else {
        multipriceOld = 0;
    }

    multipriceNew = valueCurrent * priceCurrent;
    multipriceDiff = multipriceNew - multipriceOld;

    if (multipriceNew > 0) {
        multiprice.text(multipriceNew);
    } else {
        multiprice.text("");
    }

    if (multipriceDiff != 0 && !isNaN(multipriceDiff)){
        var totalprice = $("#out_table").find("span[name='totalprice']");

        totalPriceValue = parseInt(totalprice.text());
        totalprice.text(totalPriceValue + multipriceDiff);
    }
});

function recalculateTotalPrice() {

    totalPriceValue = 0;

    $("#out_table").find(".span[name='multiprice']").each(function(i, obj) {
        multipriceValue = parseInt(obj.text());
        if (multipriceValue > 0) {
            totalPriceValue = totalPriceValue + multipriceValue
        }
    });

    $("#out_table").find(".span[name='totalprice']").text(totalPriceValue)
}

$(".input-number").keydown(function (e) {
        // Allow: backspace, delete, tab, escape, enter and .
        if ($.inArray(e.keyCode, [46, 8, 9, 27, 13, 190]) !== -1 ||
             // Allow: Ctrl+A
            (e.keyCode == 65 && e.ctrlKey === true) ||
             // Allow: home, end, left, right
            (e.keyCode >= 35 && e.keyCode <= 39)) {
                 // let it happen, don't do anything
                 return;
        }
        // Ensure that it is a number and stop the keypress
        if ((e.shiftKey || (e.keyCode < 48 || e.keyCode > 57)) && (e.keyCode < 96 || e.keyCode > 105)) {
            e.preventDefault();
        }
    });


$("#out_table").on('change',function(){

    exportCardList();
    enableSaveButons();
});

function enableSaveButons() {
    $("button[name='saveDeck']").prop('disabled', false);
    $("button[name='saveDeck']").html('<span class="glyphicon glyphicon-floppy-disk" aria-hidden="true"></span> Save')
    $("button[name='saveLibrary']").prop('disabled', false);
    $("button[name='saveLibrary']").html('<span class="glyphicon glyphicon-floppy-disk" aria-hidden="true"></span> Save')
}

$( document ).ready(function() {
    exportCardList();
});

$("#search_card_button").click(function(e){
    e.preventDefault();
    searchCard();
});
$('#search_card_input').keyup(function(e){
    if(e.keyCode == 13)
    {
        searchCard();
    }
});

$("button[name='exportCardList']").click(function(e){
    e.preventDefault();
    exportCardList();
});

function exportCardList() {
    exportText = "";

    $("#out_table tbody tr").each(function(i, obj) {

        cardname = $(this).find("span[name='cardname']").text().trim();
        edition = $(this).find("span[name='edition']").text().trim();
        count = $(this).find("input[name='count']").val();

        if (count > 0) {
            exportText += count + " x ";
            exportText += cardname;
            exportText += " [" + edition + "]";
            exportText += "\n";
        }

    });

    $("#export_card_list_panel").removeAttr('hidden')

    $("#export_card_list").text(exportText);
}

$("#saveExportedCardList").click(function(e){
    e.preventDefault();
    saveExportedCardList();
});

$("button[name='saveDeck']").click(function(e){
    e.preventDefault();
    saveDeck();
});

$("button[name='saveLibrary']").click(function(e){
    e.preventDefault();
    saveLibrary();
});

$(document).on('click', "input[name='addToDeck']", function(e){
    e.preventDefault();

    enableSaveButons();

    var card_id = $(this).attr('data-field');
    var card_row_in_deck = $("#out_table tbody").children("tr[data-field='"+card_id+"']");
    if (card_row_in_deck.length) {
        var td_count = card_row_in_deck.find("input[name='count']");
        var count = parseInt(td_count.attr('value'));
        td_count.attr('value', count + 1);
        card_row_in_deck.flashTableRow();
    } else {
        var row = $(this).closest('tr');
        var clone = row.clone();
        clone.removeClass("warning");
        clone.removeClass("info");
        clone.find("input[name='addToDeck']").remove();
        clone.find("span[name='multiprice']").text(clone.find("span[name='price']").text());
        clone.find("td.hidden").removeClass("hidden");
        clone.find("td[name='number']").addClass("hidden");
        clone.find("th[name='number']").addClass("hidden");
        clone.find("td[name='manacost']").addClass("hidden");
        clone.find("th[name='manacost']").addClass("hidden");
        $("#out_table tbody").append(clone);
        clone.flashTableRow();
    }
});

$.fn.flashTableRow = function() {
    old_bgcolor = this.css('background-color');
    old_bgcolor = 'white';
    this.css('transition', 'background-color 0.4s');
    this.css('background-color', '#fffde7');
    setTimeout(function(e) {
        e.css('background-color', old_bgcolor)
    }, 400, this);
};

function searchCard() {

    searchString = $("#search_card_input").val();

    $.ajax({
        type: "POST",
        url: 'https://localhost:5010/searchcard',
        data: {
            'search_string': searchString,
        },
        success: function(result) {
            if (result){
                $("#search_table").prop('hidden', false);
                $("#search_table").html(result);
            } else {
                alert("Something is wrong.");
            }
        },
    });
}

function saveLibrary() {

    exportCardList();
    exportText = $("#export_card_list").text();

    $.ajax({
        type: "POST",
        url: 'https://localhost:5010/savelibrary',
        data: {
            'card_list': exportText,
        },
        success: function(result) {
            if (result == "success"){
                $("button[name='saveLibrary']").html('<span class="glyphicon glyphicon-floppy-saved" aria-hidden="true"></span> Saved')
                $("button[name='saveLibrary']").prop('disabled', true)
            } else {
                alert("Cards have not been saved, something is wrong.")
            }
        },
    });
}

function saveDeck() {

    exportCardList();
    exportText = $("#export_card_list").text();

    var url = window.location.pathname;
    $.ajax({
        type: "POST",
        url: 'https://localhost:5010/modifydeck',
        data: {
            'card_list': exportText,
            'deck_id': url.split('/').pop(),
        },
        success: function(result) {
            if (result == "success"){
                $("button[name='saveDeck']").html('<span class="glyphicon glyphicon-floppy-saved" aria-hidden="true"></span> Saved')
                $("button[name='saveDeck']").prop('disabled', true)
            } else {
                alert("Cards have not been saved, something is wrong.")
            }
        },
    });
}

function saveExportedCardList() {

    exportCardList();
    exportText = $("#export_card_list").text();

    $.ajax({
        type: "POST",
        url: 'https://localhost:5010/savecards',
        data: {
            'card_list': exportText,
        },
        success: function(result) {
            if (result == "success"){
                $("#saveExportedCardList").html('Saved to Library <span class="glyphicon glyphicon-ok" aria-hidden="true"></span>')
                $("#saveExportedCardList").prop('disabled', true)
            } else {
                alert("Cards have not been saved, something is wrong.")
            }
        },
    });
}

$("a#downloadExportedCardList").click(function(){
    var text = $("#export_card_list").text();
    this.href = "data:text/plain;charset=UTF-8,"  + encodeURIComponent(text);
});

$("a#useExportedCardListAsInput").click(function(){
    var text = $("#export_card_list").text();
    $("#card_list_input_textarea").text(text);
    $("#card_list_input_form").submit(); // this is somehow not working
});

function signOut() {
  var auth2 = gapi.auth2.getAuthInstance();
  auth2.signOut().then(function () {
    console.log('User signed out.');
  });
}

function onSignIn(googleUser) {
    var profile = googleUser.getBasicProfile();
    console.log('ID: ' + profile.getId()); // Do not send to your backend! Use an ID token instead.
    console.log('Name: ' + profile.getName());
    console.log('Image URL: ' + profile.getImageUrl());
    console.log('Email: ' + profile.getEmail());

    var id_token = googleUser.getAuthResponse().id_token;

    console.log('id_token: ' + id_token);

    var xhr = new XMLHttpRequest();
    xhr.open('POST', 'https://localhost:5010/tokensignin');
    xhr.setRequestHeader('Content-Type', 'application/x-www-form-urlencoded');
    xhr.onload = function() {
      console.log('Signed in as: ' + xhr.responseText);
    };
    xhr.send('idtoken=' + id_token);
}
