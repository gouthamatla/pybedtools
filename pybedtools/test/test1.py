import pybedtools
import os, difflib
from nose.tools import assert_raises

testdir = os.path.dirname(__file__)

pybedtools.set_tempdir('.')

def fix(x):
    """
    Replaces spaces with tabs, removes spurious newlines, and lstrip()s each
    line. Makes it really easy to create BED files on the fly for testing and
    checking.
    """
    s = ""
    for i in  x.splitlines():
        i = i.strip()
        if len(i) == 0:
            continue
        i = i.split()
        i = '\t'.join(i)+'\n'
        s += i
    return s

# ----------------------------------------------------------------------------
# Streaming and non-file BedTool tests
# ----------------------------------------------------------------------------
def test_stream():
    orig_tempdir = pybedtools.get_tempdir()

    if os.path.exists('unwriteable'):
        os.system('rm -rf unwriteable')

    os.system('mkdir unwriteable')
    os.system('chmod -w unwriteable')

    a = pybedtools.example_bedtool('a.bed')
    b = pybedtools.example_bedtool('b.bed')
    c = a.intersect(b)

    pybedtools.set_tempdir('unwriteable')
    d = a.intersect(b, stream=True)
    pybedtools.set_tempdir(orig_tempdir)

    assert_raises(NotImplementedError, c.__eq__,d)
    d_contents = d.fn.read()
    c_contents = open(c.fn).read()
    assert d_contents == c_contents

    pybedtools.set_tempdir(orig_tempdir)
    c = a.intersect(b)

    pybedtools.set_tempdir('unwriteable')
    d = a.intersect(b, stream=True)

    for i,j in zip(c, d):
        assert str(i) == str(j)

    pybedtools.set_tempdir(orig_tempdir)
    os.system('rm -fr unwriteable')

def test_stream_gen():
    # these should run
    a = pybedtools.example_bedtool('a.bed')
    f = pybedtools.example_bedtool('d.gff')
    g1 = f.intersect(a)
    g2 = f.intersect(a, stream=True)

    for i,j in zip(g1, g2):
        assert str(i) == str(j)

    # this was segfaulting at one point, just run to make sure
    g3 = f.intersect(a, stream=True)
    for i in iter(g3):
        print i

def test_stream_of_stream():
    a = pybedtools.example_bedtool('a.bed')

    nonstream1 = a.intersect(a)
    stream1    = a.intersect(a, stream=True)

    assert str(nonstream1) == str(stream1)

    # Have to reconstruct stream1 cause it was consumed in the print
    nonstream1 = a.intersect(a)
    stream1    = a.intersect(a, stream=True)
    nonstream2 = a.intersect(nonstream1)
    stream2    = a.intersect(stream1, stream=True)
    assert str(nonstream2) == str(stream2)

def test_generator():
    a = pybedtools.example_bedtool('a.bed')
    b = pybedtools.BedTool(iter(a))
    expected = str(a)
    observed = str(b)
    print expected
    print observed
    assert expected == observed

    b1 = a.intersect(a)
    b2 = pybedtools.BedTool((i for i in a)).intersect(a)
    assert str(b1) == str(b2)

def test_malformed():
    a = pybedtools.BedTool("""
    chr1 100 200
    chr1 100 90
    chr1 100 200
    chr1 100 200
    chr1 100 200
    chr1 100 200
    """, from_string=True)
    a_i = iter(a)

    # first feature is OK
    print a_i.next()

    # but next one is not and should raise ValueError
    assert_raises(pybedtools.MalformedBedLineError, a_i.next)

def test_iterator():
    # makes sure we're ignoring non-feature lines

    s = """
    track name="test"


    browser position chrX:1-100
    # comment line
    chrX  1 10
    # more comments
    track name="another"


    """
    a = pybedtools.BedTool(s, from_string=True)
    results = list(a)
    assert str(results[0]) == 'chrX\t1\t10', results

# ----------------------------------------------------------------------------
# BEDTools wrapper tests
# ----------------------------------------------------------------------------

def test_bed6():
    a = pybedtools.example_bedtool('mm9.bed12')
    b = a.bed6()

def test_intersect():
    a = pybedtools.example_bedtool('a.bed')
    b = pybedtools.example_bedtool('b.bed')
    assert a.intersect(b.fn) == a.intersect(b)


    # straight-up
    expected = fix("""
    chr1 155 200 feature2 0 +
    chr1 155 200 feature3 0 -
    chr1 900 901 feature4 0 +
    """)
    assert str(a.intersect(b)) == expected

    # a that have b
    expected = fix("""
    chr1 100 200 feature2 0 +
    chr1 150 500 feature3 0 -
    chr1 900 950 feature4 0 +
    """)
    assert str(a.intersect(b,u=True)) == expected

    # stranded straight-up
    expected = fix("""
    chr1 155 200 feature3 0 -
    chr1 900 901 feature4 0 +
    """)
    assert str(a.intersect(b,s=True)) == expected

    # stranded a that have b
    expected = fix("""
    chr1 150 500 feature3 0 -
    chr1 900 950 feature4 0 +
    """)
    assert str(a.intersect(b, u=True, s=True)) == expected

    # a with no b
    expected = fix("""
    chr1 1 100 feature1 0 +
    """)
    assert str(a.intersect(b, v=True)) == expected

    # stranded a with no b
    expected = fix("""
    chr1 1   100 feature1 0 +
    chr1 100 200 feature2 0 +
    """)
    assert str(a.intersect(b, v=True, s=True)) == expected


def test_iterator():
    # makes sure we're ignoring non-feature lines
    
    s = """
    track name="test"


    browser position chrX:1-100
    # comment line
    chrX  1 10
    # more comments
    track name="another"


    """
    a = pybedtools.BedTool(s, from_string=True)
    results = list(a)
    assert str(results[0]) == 'chrX\t1\t10', results

def test_repr_and_printing():
    a = pybedtools.example_bedtool('a.bed')
    b = pybedtools.example_bedtool('b.bed')
    c = a+b
    os.unlink(c.fn)
    assert 'a.bed' in repr(a)
    assert 'b.bed' in repr(b)
    assert 'MISSING FILE' in repr(c)

    print a.head(1)

def test_bed6():
    a = pybedtools.example_bedtool('mm9.bed12')
    b = a.bed6()

def test_introns():
    a = pybedtools.example_bedtool('mm9.bed12')
    t = pybedtools.BedTool._tmp()
    b = pybedtools.BedTool((f for f in a if f.name == "Tcea1,uc007afj.1"))
    b.saveas(t)
    b = pybedtools.BedTool(t)
    bfeat = iter(b).next()

    bi = b.introns()
    # b[9] is the exonCount from teh bed12 file. there should be
    # b[9] -1 introns assuming no utrs.
    assert len(bi) == int(bfeat[9]) - 1, (len(bi), len(b))


def test_intersect():
    a = pybedtools.example_bedtool('a.bed')
    b = pybedtools.example_bedtool('b.bed')
    assert a.intersect(b.fn) == a.intersect(b)


    # straight-up
    expected = fix("""
    chr1 155 200 feature2 0 +
    chr1 155 200 feature3 0 -
    chr1 900 901 feature4 0 +
    """)
    assert str(a.intersect(b)) == expected
    
    # a that have b
    expected = fix("""
    chr1 100 200 feature2 0 +
    chr1 150 500 feature3 0 -
    chr1 900 950 feature4 0 +
    """)
    assert str(a.intersect(b,u=True)) == expected
    
    # stranded straight-up
    expected = fix("""
    chr1 155 200 feature3 0 -
    chr1 900 901 feature4 0 +
    """)
    assert str(a.intersect(b,s=True)) == expected

    # stranded a that have b
    expected = fix("""
    chr1 150 500 feature3 0 -
    chr1 900 950 feature4 0 +
    """)
    assert str(a.intersect(b, u=True, s=True)) == expected

    # a with no b
    expected = fix("""
    chr1 1 100 feature1 0 +
    """)
    assert str(a.intersect(b, v=True)) == expected

    # stranded a with no b
    expected = fix("""
    chr1 1   100 feature1 0 +
    chr1 100 200 feature2 0 +
    """)
    assert str(a.intersect(b, v=True, s=True)) == expected

def test_subtract():
    a = pybedtools.example_bedtool('a.bed')
    b = pybedtools.example_bedtool('b.bed')

    # plain 'old subtract
    results = str(a.subtract(b))
    expected = fix("""
    chr1	1	100	feature1	0	+
    chr1	100	155	feature2	0	+
    chr1	150	155	feature3	0	-
    chr1	200	500	feature3	0	-
    chr1	901	950	feature4	0	+""")
    assert results == expected

    # strand-specific
    results = str(a.subtract(b,s=True))
    print results
    expected = fix("""
    chr1	1	100	feature1	0	+
    chr1	100	200	feature2	0	+
    chr1	150	155	feature3	0	-
    chr1	200	500	feature3	0	-
    chr1	901	950	feature4	0	+""")
    assert results == expected

    # the difference in f=0.2 and f=0.1 is in feature5 of b.  Since feature2
    # and feature3 of a overlap, it's seeing the 'a' feature as a 399-bp
    # feature (chr1:100-500), and feature5 of 'b' overlaps this by 44 bp.
    #
    # So the threshold fraction should be
    #
    #   44/399 = 0.1103 
    #
    # f > 0.1103 should return no subtractions, because nothing in b overlaps by that much.
    # However, 0.12 doesn't work; need to go to 0.13 . . .
    results = str(a.subtract(b,s=True,f=0.13))
    expected = fix("""
    chr1	1	100	feature1	0	+
    chr1	100	200	feature2	0	+
    chr1	150	500	feature3	0	-
    chr1	900	950	feature4	0	+""")
    assert results == expected

    # f < 0.1103, so should get a subtraction
    results = str(a.subtract(b,s=True,f=0.1))
    print results
    expected = fix("""
    chr1	1	100	feature1	0	+
    chr1	100	200	feature2	0	+
    chr1	150	155	feature3	0	-
    chr1	200	500	feature3	0	-
    chr1	900	950	feature4	0	+""")
    assert results == expected

def test_slop():
    a = pybedtools.example_bedtool('a.bed')

    results = str(a.slop(g=pybedtools.chromsizes('hg19'), b=100))
    expected = fix("""
    chr1	0	200	feature1	0	+
    chr1	0	300	feature2	0	+
    chr1	50	600	feature3	0	-
    chr1	800	1050	feature4	0	+
    """)
    assert results == expected

    results = str(a.slop(g=pybedtools.chromsizes('hg19'), l=100, r=1))
    expected = fix("""
    chr1	0	101	feature1	0	+
    chr1	0	201	feature2	0	+
    chr1	50	501	feature3	0	-
    chr1	800	951	feature4	0	+
    """)
    assert results == expected


    # Make sure it complains if no genome is set
    assert_raises(ValueError, a.slop, **dict(l=100, r=1))

    # OK, so set one...
    a.set_chromsizes(pybedtools.chromsizes('hg19'))

    # Results should be the same as before.
    results = str(a.slop(l=100, r=1))
    expected = fix("""
    chr1	0	101	feature1	0	+
    chr1	0	201	feature2	0	+
    chr1	50	501	feature3	0	-
    chr1	800	951	feature4	0	+
    """)
    print results
    assert results == expected

def test_merge():
    a = pybedtools.example_bedtool('a.bed')
    results = str(a.merge())
    expected = fix("""
    chr1	1	500
    chr1	900	950
    """)
    assert results == expected

    results = str(a.merge(s=True))
    expected = fix("""
    chr1	1	200	+
    chr1	900	950	+
    chr1	150	500	-
    """)
    assert results == expected

    b = pybedtools.example_bedtool('b.bed')
    results = str(b.merge(d=700))
    expected = fix("""
    chr1 155 901 
    """)
    print results
    assert results == expected

def test_closest():
    a = pybedtools.example_bedtool('a.bed')
    b = pybedtools.example_bedtool('b.bed')
    r = a.closest(b)
    assert len(r) == len(a)

# TODO: there's enough stuff in here that it's probably worth it to eventually
# make a TestSequenceStuff class
def test_sequence():
    """
    From UCSC:

    chromStart - The starting position of the feature in the chromosome or
    scaffold. The first base in a chromosome is numbered 0.

    chromEnd - The ending position of the feature in the chromosome or
    scaffold. The chromEnd base is not included in the display of the feature.
    For example, the first 100 bases of a chromosome are defined as
    chromStart=0, chromEnd=100, and span the bases numbered 0-99. """

    fi = os.path.join(testdir, 'test.fasta')

    s = """
    chrX 9  16 . . +
    chrX 9  16 . . -
    chrY 1  4  . . +
    chrZ 28 31 . . +
    """

    fasta = """
    >chrX
    AAAAAAAAATGCACTGAAAAAAAAAAAAAAA
    >chrY
    GCTACCCCCCCCCCCCCCCCCCCCCCCCCCC
    >chrZ
    AAAAAAAAAAAAAAAAAAAAAAAAAAAATCT
    """
    a = pybedtools.BedTool(s, from_string=True)
    assert_raises(ValueError, a.save_seqs, ('none',))

    fout = open(fi,'w')
    for line in fasta.splitlines(True):
        fout.write(line.lstrip())
    fout.close()

    f = a.sequence(fi=fi)
    assert f.fn == f.fn
    seqs = open(f.seqfn).read()
    print seqs
    expected = """>chrX:9-16
TGCACTG
>chrX:9-16
TGCACTG
>chrY:1-4
CTA
>chrZ:28-31
TCT
"""
    print ''.join(difflib.ndiff(seqs,expected))
    print expected 
    assert seqs == expected

    f = a.sequence(fi=fi,s=True)
    seqs = open(f.seqfn).read()
    expected = """>chrX:9-16(+)
TGCACTG
>chrX:9-16(-)
CAGTGCA
>chrY:1-4(+)
CTA
>chrZ:28-31(+)
TCT
"""
    print seqs
    print expected
    print ''.join(difflib.ndiff(seqs,expected))
    assert seqs == expected

    f = f.save_seqs('deleteme.fa')
    assert open('deleteme.fa').read() == expected
    assert f.print_sequence() == expected
    os.unlink('deleteme.fa')

    fresh_a = pybedtools.BedTool(s, from_string=True)
    assert fresh_a == f

    os.unlink(fi)
    if os.path.exists(fi+'.fai'):
        os.unlink(fi+'.fai')

# ----------------------------------------------------------------------------
# Operator tests
# ----------------------------------------------------------------------------
def test_add_subtract():
    a = pybedtools.example_bedtool('a.bed')
    b = pybedtools.example_bedtool('b.bed')
    assert a.intersect(b,u=True) == (a+b)
    assert a.intersect(b,v=True) == (a-b)

def test_subset():
    a = pybedtools.example_bedtool('a.bed')
    import random
    random.seed(1)

    s = list(a.random_subset(1).features())
    assert len(s) == 1
    assert isinstance(s[0], pybedtools.Interval)

    s2 = list(a.random_subset(len(a)).features())
    print len(s2)
    assert len(s2) == len(a)

def test_eq():
    a = pybedtools.example_bedtool('a.bed')
    b = pybedtools.example_bedtool('a.bed')

    # BedTool to BedTool
    assert a == b

    # BedTool to string
    assert a == """chr1	1	100	feature1	0	+
chr1	100	200	feature2	0	+
chr1	150	500	feature3	0	-
chr1	900	950	feature4	0	+
"""
    # Test not equa on bedtool
    b = pybedtools.example_bedtool('b.bed')
    assert b != a

    # and string
    assert a != "blah"

    # Don't allow testing equality on streams
    c = a.intersect(b, stream=True)
    d = a.intersect(b)
    assert_raises(NotImplementedError, c.__eq__, d)
    assert_raises(NotImplementedError, d.__eq__, c)

    # Test it on iterator, too....
    e = pybedtools.BedTool((i for i in a))
    assert_raises(NotImplementedError, e.__eq__, a)
    assert_raises(NotImplementedError, a.__eq__, e)

    # Make sure that if we force the iterator to be consumed, it is in fact
    # equal
    assert a == str(e)


# ----------------------------------------------------------------------------
# Other BedTool method tests
# ----------------------------------------------------------------------------

def test_count_bed():
    a = pybedtools.example_bedtool('a.bed')
    assert a.count() == 4
    assert len(a) == 4

def test_feature_centers():
    from pybedtools import featurefuncs
    a = pybedtools.BedTool("""
                           chr1 1 100
                           chr5 3000 4000
                           """, from_string=True)
    b = a.each(featurefuncs.center, 1)
    results = list(b.features())

    print results

    assert results[0].start == 50
    assert results[0].stop == 51
    assert results[0].chrom == 'chr1'

    assert results[1].start == 3500
    assert results[1].stop == 3501
    assert results[1].chrom == 'chr5'

def test_bedtool_creation():
    # make sure we can make a bedtool from a bedtool and that it points to the
    # same file
    a = pybedtools.example_bedtool('a.bed')
    b = pybedtools.BedTool(a)
    assert b.fn == a.fn
    assert_raises(ValueError, pybedtools.BedTool,'nonexistent.bed')

    # note that *s* has both tabs and spaces....
    s = """
    chr1	1	100	feature1  0	+
    chr1	100	200	feature2  0	+
    chr1	150	500	feature3  0	-
    chr1	900	950	feature4  0	+
    """
    from_string = pybedtools.BedTool(s, from_string=True)

    # difflib used here to show a bug where a newline was included when using
    # from_string
    print ''.join(difflib.ndiff(str(from_string), str(a)))

    assert str(from_string) == str(a)

def test_special_methods():
    # note that *s* has both tabs and spaces....
    s = """
    chr1	1	100	feature1  0	+
    chr1	100	200	feature2  0	+
    chr1	150	500	feature3  0	-
    chr1	900	950	feature4  0	+
    """
    from_string = pybedtools.BedTool(s, from_string=True)
    a = pybedtools.example_bedtool('a.bed')
    b = pybedtools.example_bedtool('b.bed')

    assert from_string == a
    assert from_string != b
    assert not from_string == b
    assert not from_string != a

def test_field_count():
    a = pybedtools.example_bedtool('a.bed')
    assert a.field_count() == 6

def test_cat():
    a = pybedtools.example_bedtool('a.bed')
    b = pybedtools.example_bedtool('b.bed')
    c = a.cat(b, postmerge=False)
    assert len(a) + len(b) == len(c), (len(a), len(b), len(c))

def test_repr_and_printing():
    a = pybedtools.example_bedtool('a.bed')
    b = pybedtools.example_bedtool('b.bed')
    c = a+b
    os.unlink(c.fn)
    assert 'a.bed' in repr(a)
    assert 'b.bed' in repr(b)
    assert 'MISSING FILE' in repr(c)

    print a.head(1)

def test_cut():
    a = pybedtools.example_bedtool('a.bed')
    c = a.cut([0, 1, 2, 4])
    assert c.field_count() == 4, c

def test_filter():
    a = pybedtools.example_bedtool('a.bed')

    b = a.filter(lambda f: f.length < 100 and f.length > 0)
    assert len(b) == 2

def test_random_intersection():
    # TODO:
    return
    N = 4
    a = pybedtools.example_bedtool('a.bed')
    b = pybedtools.example_bedtool('b.bed')
    li = list(a.randomintersection(b, N))
    assert len(li) == N, li

def test_cat():
    a = pybedtools.example_bedtool('a.bed')
    b = pybedtools.example_bedtool('b.bed')
    b_fn = pybedtools.example_filename('b.bed')
    assert a.cat(b) == a.cat(b_fn)
    expected =  fix("""
    chr1 1   500
    chr1 800 950
    """)
    assert a.cat(b) == expected



# ----------------------------------------------------------------------------
# Interval tests
# ----------------------------------------------------------------------------

def test_gff_stuff():
    s = """
    chr1  fake  gene 1 100 . + . ID=gene1
    chr1  fake  mRNA 1 100 . + . Name=mRNA1
    chr1  fake  CDS 50 90 . + . other=nothing
    """
    d = pybedtools.BedTool(s, from_string=True)
    f1, f2, f3 = d.features()
    assert f1.name == 'gene1', f1.name
    assert f2.name == 'mRNA1', f2.name
    assert f3.name is None, f3.name

def test_name():
    c = iter(pybedtools.example_bedtool('c.gff')).next()
    assert c.name == "thaliana_1_465_805" , c.name

# ----------------------------------------------------------------------------
# Other tests
# ----------------------------------------------------------------------------

def test_flatten():
    from pybedtools.helpers import _flatten_list 
    result = _flatten_list([[1,2,3,0,[0,5],9],[100]])
    print result
    assert result == [1, 2, 3, 0, 0, 5, 9, 100]

def test_history_step():
    a = pybedtools.example_bedtool('a.bed')
    b = pybedtools.example_bedtool('b.bed')
    c = a.intersect(b)
    d = c.subtract(a)

    print d.history
    d.delete_temporary_history(ask=True, raw_input_func=lambda x: 'n')
    assert os.path.exists(a.fn)
    assert os.path.exists(b.fn)
    assert os.path.exists(c.fn)
    assert os.path.exists(d.fn)

    d.delete_temporary_history(ask=True, raw_input_func=lambda x: 'Yes')
    assert os.path.exists(a.fn)
    assert os.path.exists(b.fn)
    assert not os.path.exists(c.fn) # this is the only thing that should change
    assert os.path.exists(d.fn)

    a = pybedtools.example_bedtool('a.bed')
    b = pybedtools.example_bedtool('b.bed')
    c = a.intersect(b)
    d = c.subtract(a)
    d.delete_temporary_history(ask=False)
    assert os.path.exists(a.fn)
    assert os.path.exists(b.fn)
    assert not os.path.exists(c.fn) # this is the only thing that should change
    assert os.path.exists(d.fn)

def test_kwargs():
    a = pybedtools.example_bedtool('a.bed')
    b = a.intersect(a, s=False)
    c = a.intersect(a)
    assert str(b) == str(c)

def teardown():
    # always run this!
    pybedtools.cleanup(remove_all=True)
