from html.parser import HTMLParser
class Node:
    def __init__(self,tag='',attrs=()):self.tag=tag;self.attrs=dict(attrs);self.children=[]
    def all(self,predicate):
        out=[]
        for x in self.children:
            if isinstance(x,Node):
                if predicate(x):out.append(x)
                out.extend(x.all(predicate))
        return out
    def text(self):return ''.join(x.text() if isinstance(x,Node) else x for x in self.children).strip()
    def first(self,p):return self.all(p)[0]

class DOM(HTMLParser):
    def __init__(self,text):
        super().__init__(convert_charrefs=True);self.root=Node();self.stack=[self.root];self.feed(text)
    def handle_starttag(self,tag,attrs):
        n=Node(tag,attrs);self.stack[-1].children.append(n)
        if tag not in ('area','base','br','col','embed','hr','img','input','link','meta','param','source','track','wbr'):self.stack.append(n)
    def handle_startendtag(self,tag,attrs):self.stack[-1].children.append(Node(tag,attrs))
    def handle_endtag(self,tag):
        for i in range(len(self.stack)-1,0,-1):
            if self.stack[i].tag==tag:self.stack=self.stack[:i];break
    def handle_data(self,data):self.stack[-1].children.append(data)

def has(a):return lambda n:a in n.attrs
def cls(c):return lambda n:c in n.attrs.get('class','').split()

