// Korean full-won words used in the A4 portrait invoice. No external dependencies.
// "일백" / "일천" are intentionally explicit for accounting-style wording.
const digitWords=['','일','이','삼','사','오','육','칠','팔','구'];
const smallUnits=['','십','백','천'];
const largeUnits=['','만','억','조'];
const numberFormatter=new Intl.NumberFormat('ko-KR');

export function koreanWonText(value){
 const amount=Number(value);
 if(!Number.isSafeInteger(amount)||amount<0||amount>=10**16){
  return '금액 확인 필요';
 }
 if(amount===0)return '영원 정 (₩0)';
 let rest=amount,index=0;
 const fragments=[];
 while(rest>0){
  const group=rest%10000;
  if(group){
   let words='';
   for(let i=3;i>=0;i--){
    const digit=Math.floor(group/10**i)%10;
    if(digit)words+=digitWords[digit]+smallUnits[i];
   }
   fragments.unshift(words+largeUnits[index]);
  }
  rest=Math.floor(rest/10000);
  index++;
 }
 return fragments.join('')+'원 정 (₩'+numberFormatter.format(amount)+')';
}
