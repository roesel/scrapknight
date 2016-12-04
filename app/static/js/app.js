//plugin bootstrap minus and plus
//http://jsfiddle.net/laelitenetwork/puJ6G/
$('.btn-number').click(function(e){
    e.preventDefault();

    fieldName = $(this).attr('data-field');
    type      = $(this).attr('data-type');
    var input = $("input[data-field='"+fieldName+"']");
    var currentVal = parseInt(input.val());
    if (!isNaN(currentVal)) {
        if(type == 'minus') {

            if(currentVal > input.attr('min')) {
                input.val(currentVal - 1).change();
            }
            if(parseInt(input.val()) == input.attr('min')) {
                $(this).attr('disabled', true);
            }

        } else if(type == 'plus') {

            if(currentVal < input.attr('max')) {
                input.val(currentVal + 1).change();
            }
            if(parseInt(input.val()) == input.attr('max')) {
                $(this).attr('disabled', true);
            }

        }
    } else {
        input.val(0);
    }
});
$('.input-number').focusin(function(){
   $(this).data('oldValue', $(this).val());
});
$('.input-number').change(function() {

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

    var price = $("span[name='price'][data-field='"+df+"']");
    var multiprice = $("span[name='multiprice'][data-field='"+df+"']");

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
        var totalprice = $("span[name='totalprice']");

        totalPriceValue = parseInt(totalprice.text());
        totalprice.text(totalPriceValue + multipriceDiff);
    }
});

function recalculateTotalPrice() {

    totalPriceValue = 0;

    $(".span[name='multiprice']").each(function(i, obj) {
        multipriceValue = parseInt(obj.text());
        if (multipriceValue > 0) {
            totalPriceValue = totalPriceValue + multipriceValue
        }
    });

    $(".span[name='totalprice']").text(totalPriceValue)
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
