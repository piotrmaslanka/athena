var interval_variable = null;
var current_question_id = null;
var is_first_time = true;

var was_answered = [];

function esctext(txt) { return $('<div>/').text(txt).html(); }

function tophdr_time_timer(intv) {
    // Update the tophdr timer
    if (interval_variable != null) clearInterval(interval_variable);
    if (intv <= 0) { do_a_heartbeat(); return; }
    
    var k = ''+Math.floor(intv/60)+'min '+Math.floor(intv % 60)+'s';
    
    $('#opfield .tophdr .time').html(k);
    interval_variable = setInterval(function() { tophdr_time_timer(intv-1) }, 1000);
}

function process_response(data) {   // a response was received and it should be processed
    $('#opfield').empty();
    if (data.status == 'wait') {
        $('#opfield').html('<div class="largedisclaimer">Czekaj na dostępność egzaminu</div>');
        setTimeout(do_a_heartbeat, 5000);
    }
    
    if (data.status == 'finished') {
        $('#opfield').html('<div class="largedisclaimer">Egzamin ukończony. Ocena: '+data.grade+'</div><div class="subdisclaimer">W zakładce Wyniki możesz obejrzeć ocenę</div>');
        
        if (data.protocol == null) return;
        // gosh. Present the protocol if applicable.
    }
    
    if (data.status == 'content') {
        var opfield = $('#opfield');
        opfield.empty();
        
        if ((data.question_id == 0) && (is_first_time)) {
            // instead of presenting the question, present the test rules
            var rfield = $('<div id="rfield">');
            rfield.append('<p style="font-weight: bold;">PRZECZYTAJ UWAŻNIE PONIŻSZE INFORMACJE</p>');
            var ul = $('<ul></ul>');
            
            ul.append('<li>Za chwilę napiszesz test z '+data.testname+'</li>');
            if (data.exam_name == 'DEMO EGZAMIN')
                ul.append('<li>Jest to egzamin demonstracyjny</li>');
            else
                ul.append('<li>Jest to egzamin NA PRAWDĘ</li>');
            
            ul.append('<li>Odpowiesz na '+data.tot_questions+' pytań '+(data.is_multichoice ? 'wielokrotnego wyboru' : 'jednokrotnego wyboru')+'</li>');
            
            ul.append('<li>Zaznaczaj odpowiedzi poprawne</li>');
            
            if (data.can_go_back) ul.append('<li>Możesz odpowiadać na pytania w dowolnej kolejności</li>');
            if (data.total_test_time == null) 
                ul.append('<li>Na każde pytanie jest osobna pula czasu</li>');
            else {
                var minutes = Math.floor(data.total_test_time / 60);
                var seconds = Math.floor(data.total_test_time % 60);
                ul.append('<li>Na wykonanie testu masz '+minutes+' minut' + (seconds == 0 ? '' : ' i '+seconds+' sekund')+'</li>');
            }
            
            rfield.append(ul);

            var btn = $('<div class="accept">ROZPOCZNIJ</div>');
            is_first_time = false;
            btn.click(function() {
                $.post('/test/ajax/', {'command': 'presented'}, process_response);
                current_question_id = data.question_id;                
            });
            rfield.append(btn);
            opfield.append(rfield);
            return;            
        }        

        // Construct a header
        var hdr = $('<div class="tophdr"><div class="name">'+data.testname+'</div>');    
        if (data.time_remaining != null) hdr.append('<div class="time"></div>');
        opfield.append(hdr);
        opfield.append('<hr style="clear: both;">');
        if (data.time_remaining != null) tophdr_time_timer(data.time_remaining);

        // Construct the question selection space 
        var qlspace = $('<div class="qlspace"></div>');
                
        for (var i=0; i<data.tot_questions; i++) {
            var elem = $('<div class="i">'+(i+1)+'</div>');
            if (!data.can_go_back) elem.css('cursor', 'auto');
            if (data.question_id == i) elem.addClass('this');
            if (was_answered.indexOf(i) != -1) elem.addClass('answered');
            function switchto_maker(x) { return function() { switchto(x); }}
            
            if (data.can_go_back) elem.click(switchto_maker(i));
            qlspace.append(elem);
        }
        opfield.append(qlspace);
                
        // Construct the question space
        var qspace = $('<div class="qspace"></div>');
        qspace.append(esctext(data.question_content).replace('\n', '<br>'));

        if (data.question_attachment != null) 
            qspace.append('<div style="width: 800px; text-align: center;"><img src="'+data.question_attachment+'" alt="Załącznik" style="max-width: 800px;"></div>');

        opfield.append(qspace);

        // Construct the answer space
        var aspace = $('<div class="aspace"></div>');
        for (var i=0; i<data.answers.length; i++) {
            var answer_content = data.answers[i][0];
            var answer_is_ticked = data.answers[i][1];
            
            // generate radiobox
            if (data.is_multichoice) {
                var answ = $('<input type="checkbox" id="answ'+i+'"'+(answer_is_ticked ? ' checked' : '')+'>');
            } else {
                var answ = $('<input type="radio" name="radio" id="answ'+i+'"'+(answer_is_ticked ? ' checked' : '')+'>');                
            }
            var answ2 = $('<div class="answer"></div>');
            answ2.append(answ);
            answ2.append(esctext(answer_content).replace('\n', '<br>'));
            aspace.append(answ2);
        }

        var answer_button = $('<div id="answer_button">Odpowiedz</div>');
        answer_button.click(function() {
            // compile answer values
            var answers = [];
            for (var i=0;$('#answ'+i).length>0;i++)
                answers.push($('#answ'+i).is(':checked'));
            $.post('/test/ajax/', {'command': 'answer', 
                                   'answers': JSON.stringify(answers)}, process_response);
            was_answered.push(current_question_id);
        });
        aspace.append(answer_button);

        if (data.can_go_back) {
        var endtest_button = $('<div id="endtest_button">Zakończ test</div>');
        endtest_button.click(function() {
            if (!confirm('Czy na pewno chcesz skończyć test? Pamiętaj że wszystkie odpowiedzi muszą być potwierdzone guzikiem Odpowiedz aby zostały zaliczone!')) return;
            $.post('/test/ajax/', {'command': 'finish'}, process_response);                    
        });
            aspace.append(endtest_button);
        }

        opfield.append(aspace);

        var qlspace = $('<div class="qlspace"></div>');        
        if (data.can_go_back) {
            if (data.question_id > 0) {
                var l = $('<div class="prev">&#8656</div>').click(function() {                    
                    switchto(data.question_id-1);
                });
                qlspace.append(l);
            }
            if (data.question_id < (data.tot_questions-1)) {
                var l = $('<div class="next">&#8658</div>').click(function() {                    
                    switchto(data.question_id+1);
                });
                qlspace.append(l);
            }
            qlspace.append('<div class="sep"></div>');
        }
        
        opfield.append(qlspace);
        
        if (data.question_id != current_question_id) {
            // question just presented, sent a presentation notification
            $.post('/test/ajax/', {'command': 'presented'}, process_response);
            current_question_id = data.question_id;
        }
        // Dadadada all stuff done :)
    }
}

function switchto(qid) {    // requests a question switch
    $.post('/test/ajax/', {'command': 'switchto', 'qid': qid}, process_response);
}

function do_a_heartbeat() {  // doubles as do-a-heartbeat
    $.post('/test/ajax/', {'command': 'heartbeat'}, process_response);
}

$(do_a_heartbeat);